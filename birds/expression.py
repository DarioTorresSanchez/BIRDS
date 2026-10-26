"""Safe arithmetic-expression evaluator for bivariate / spider axes.

The user can type expressions in any axis combo of the bivariate view, such
as ``La/Yb``, ``Ti/1000``, ``(La+Ce)/2`` or ``log(Sr/Y)``.  This module
parses such strings with :mod:`ast` and evaluates them against a pandas
``DataFrame``, using a strict white-list of operators and functions so the
input is *never* fed to :func:`eval` directly.

Public entry points
-------------------
``evaluate(df, text) -> pd.Series``
    Return the numeric series obtained by evaluating *text* on *df*.

``evaluate_scalar(values, text) -> float | None``
    Same as :func:`evaluate` but takes a ``Mapping[str, float]`` and
    returns a scalar.  Used to evaluate reservoir compositions
    (PM, N-MORB, OIB, …) on derived axes.

``is_expression(text) -> bool``
    Cheap heuristic: returns ``True`` iff *text* contains any arithmetic
    operator or parenthesis.

``is_simple_column(df, text) -> bool``
    ``True`` iff *text* matches an existing column name verbatim.

Supported syntax
----------------
* Binary operators: ``+ - * / **``
* Unary operators: ``+ -``
* Function calls (single argument): ``log``, ``ln``, ``log10``, ``exp``,
  ``sqrt``, ``abs``
* Numeric literals (int/float)
* Identifiers — must match a column name in *df* (or the keys passed to
  :func:`evaluate_scalar`).
* Derived variables — ``Mg#``, ``Mg#_FeOt`` and ``Mg#_adj`` (see
  :mod:`birds.derived`), alone or inside an expression such as
  ``Mg#_FeOt/100``.
* Parentheses

Anything else raises :class:`ExpressionError`.
"""

from __future__ import annotations

import ast
import operator
from typing import Mapping, Optional

import numpy as np
import pandas as pd


class ExpressionError(ValueError):
    """Raised when an expression cannot be parsed or evaluated."""


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

_UNARY_OPS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_FUNCS = {
    "log": np.log,        # natural log
    "ln":  np.log,        # alias
    "log10": np.log10,
    "exp": np.exp,
    "sqrt": np.sqrt,
    "abs": np.abs,
}


# ``#`` opens a comment in Python, so ``Mg#`` cannot reach the parser as
# written.  Each derived name is swapped for a placeholder identifier
# first -- longest first, so ``Mg#_adj`` is not read as ``Mg#`` + ``_adj``.
_DERIVED_TOKENS = {
    "Mg#_FeOt": "__derived_mg_number_feot__",
    "Mg#_adj": "__derived_mg_number_adj__",
    "Mg#": "__derived_mg_number__",
}
_TOKEN_NAMES = {token: name for name, token in _DERIVED_TOKENS.items()}


def _substitute_derived(text: str) -> str:
    for name, token in _DERIVED_TOKENS.items():
        text = text.replace(name, token)
    return text


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def is_expression(text: str) -> bool:
    """Cheap heuristic: does *text* look like an expression rather than a
    bare column name?"""
    if not text:
        return False
    return any(ch in text for ch in "+-*/()")


def is_simple_column(df: pd.DataFrame, text: str) -> bool:
    """``True`` iff *text* is exactly a column of *df*."""
    return text.strip() in df.columns


def evaluate(df: pd.DataFrame, text: str) -> pd.Series:
    """Evaluate the arithmetic expression *text* against the columns of
    *df*.

    Parameters
    ----------
    df :
        DataFrame whose numeric columns are used as variables.  Columns are
        coerced to numeric with ``errors='coerce'`` so non-numeric entries
        become ``NaN``.
    text :
        The expression.  If it matches an existing column name exactly the
        column is returned directly (fast path, preserves dtype).

    Returns
    -------
    pd.Series
        Result aligned with ``df.index``.  Scalar expressions are
        broadcast.

    Raises
    ------
    ExpressionError
        On parse error, unknown column / function, unsupported operator.
    """
    if text is None:
        raise ExpressionError("Empty expression")
    text = text.strip()
    if not text:
        raise ExpressionError("Empty expression")

    # Fast path: bare column reference
    if text in df.columns:
        return pd.to_numeric(df[text], errors="coerce")

    try:
        tree = ast.parse(_substitute_derived(text), mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"Syntax error in '{text}': {exc.msg}") from exc

    result = _eval_node(tree.body, df_source=df)
    if not isinstance(result, pd.Series):
        # Scalar result (e.g. user typed "100"): broadcast to full length
        result = pd.Series([float(result)] * len(df), index=df.index)
    return result


def evaluate_scalar(values: Mapping[str, float], text: str) -> Optional[float]:
    """Evaluate *text* on a single-row mapping of ``column -> value``.

    Used to evaluate reservoir compositions on derived axes (e.g. compute
    *La/Yb* for the Primitive Mantle reservoir).  Returns ``None`` when
    any referenced column is missing — this means the reservoir simply
    skips that overlay.
    """
    if not text:
        return None
    text = text.strip()
    if not text:
        return None

    # Fast path: bare column reference
    if text in values:
        v = values[text]
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    try:
        tree = ast.parse(_substitute_derived(text), mode="eval")
    except SyntaxError:
        return None

    try:
        result = _eval_node(tree.body, scalar_source=values)
    except ExpressionError:
        return None
    if result is None:
        return None
    try:
        out = float(result)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(out):
        return None
    return out


# ---------------------------------------------------------------------------
# AST walker
# ---------------------------------------------------------------------------

def _eval_node(node: ast.AST, *, df_source: Optional[pd.DataFrame] = None,
               scalar_source: Optional[Mapping[str, float]] = None):
    """Recursively evaluate *node*.

    Exactly one of ``df_source`` / ``scalar_source`` should be provided.
    For ``df_source`` the result of identifier lookups is a ``pd.Series``;
    for ``scalar_source`` it is a ``float``.
    """
    # Literal numbers ------------------------------------------------------
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise ExpressionError("Booleans not allowed")
        if not isinstance(node.value, (int, float)):
            raise ExpressionError(f"Unsupported literal: {node.value!r}")
        return float(node.value)

    # Identifiers ---------------------------------------------------------
    if isinstance(node, ast.Name):
        name = _TOKEN_NAMES.get(node.id, node.id)
        if df_source is not None:
            if name in df_source.columns:
                return pd.to_numeric(df_source[name], errors="coerce")
            if node.id in _TOKEN_NAMES:
                from .derived import derived_series
                series = derived_series(df_source, name)
                if series is None:
                    from .derived import DESCRIPTIONS
                    raise ExpressionError(
                        f"'{name}' cannot be computed from these data. "
                        f"{DESCRIPTIONS.get(name, '')}")
                return series
            raise ExpressionError(
                f"Unknown column '{name}'. "
                f"Available: {', '.join(map(str, df_source.columns[:8]))}…"
            )
        if scalar_source is not None:
            if name in scalar_source:
                v = scalar_source[name]
                if v is None:
                    raise ExpressionError(f"'{name}' has no value")
                return float(v)
            if node.id in _TOKEN_NAMES:
                from .derived import derived_scalar
                v = derived_scalar(scalar_source, name)
                if v is None:
                    raise ExpressionError(f"'{name}' has no value")
                return v
            # Reference compositions are published volatile-free, so an
            # axis on adjusted majors reads their plain values.
            base = name[:-len("_adj")] if name.endswith("_adj") else None
            if base and scalar_source.get(base) is not None:
                return float(scalar_source[base])
            raise ExpressionError(f"Unknown variable '{name}'")
        raise ExpressionError("No data source provided")

    # Binary operators ----------------------------------------------------
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise ExpressionError(
                f"Operator not allowed: {op_type.__name__}"
            )
        left = _eval_node(node.left, df_source=df_source,
                          scalar_source=scalar_source)
        right = _eval_node(node.right, df_source=df_source,
                           scalar_source=scalar_source)
        with np.errstate(divide="ignore", invalid="ignore"):
            return _BIN_OPS[op_type](left, right)

    # Unary operators -----------------------------------------------------
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise ExpressionError(
                f"Unary operator not allowed: {op_type.__name__}"
            )
        operand = _eval_node(node.operand, df_source=df_source,
                             scalar_source=scalar_source)
        return _UNARY_OPS[op_type](operand)

    # Function calls ------------------------------------------------------
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ExpressionError("Only simple function calls are allowed")
        fname = node.func.id
        if fname not in _FUNCS:
            allowed = ", ".join(sorted(_FUNCS))
            raise ExpressionError(
                f"Function '{fname}' not allowed. Available: {allowed}"
            )
        if node.keywords:
            raise ExpressionError("Keyword arguments not allowed")
        if len(node.args) != 1:
            raise ExpressionError(
                f"Function '{fname}' expects exactly 1 argument"
            )
        arg = _eval_node(node.args[0], df_source=df_source,
                         scalar_source=scalar_source)
        with np.errstate(divide="ignore", invalid="ignore"):
            return _FUNCS[fname](arg)

    raise ExpressionError(
        f"Unsupported syntax: {type(node).__name__}"
    )

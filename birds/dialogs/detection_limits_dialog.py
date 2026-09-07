"""Change the below-detection substitution policy after the import.

The policy is chosen in the Import dialog, but the choice is a
methodological one a reviewer may well question — and comparing x/2
against x/√2 should not cost a full re-import and the loss of every
plot setting.  Because the reported limits are kept alongside the
flags (:class:`~birds.detection_limits.BdlReport`), switching is just
a recomputation of the flagged cells.
"""

from __future__ import annotations


from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from ..detection_limits import POLICIES, POLICY_LABELS, reapply_policy

_SHEET_TITLES = {
    "main": "Data",
    "isotopes": "Isotopes",
    "petrography": "Petrography",
}


class DetectionLimitsDialog(QDialog):
    """Pick a substitution policy and reapply it to every loaded sheet."""

    def __init__(self, data, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Detection limits")
        self.setMinimumWidth(460)
        self.data = data
        self.n_changed = 0

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self._inventory_html()))

        form = QFormLayout()
        self.policy_combo = QComboBox()
        for pol in POLICIES:
            self.policy_combo.addItem(POLICY_LABELS.get(pol, pol), pol)
        current = getattr(data, "bdl_policy", "half")
        idx = self.policy_combo.findData(current)
        if idx >= 0:
            self.policy_combo.setCurrentIndex(idx)
        form.addRow("Substitution:", self.policy_combo)
        layout.addLayout(form)

        note = QLabel(
            "<span style='color:#8a6d1a;'>Only cells with a reported "
            "limit (<i>&lt;x</i>) change. Textual markers "
            "(<i>b.d.l.</i>, <i>n.d.</i>) carry no limit and stay blank "
            "under every policy.<br>If you have already run "
            "Pre-process, run it again afterwards so the rewritten "
            "cells are rescaled with the rest.</span>")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._buttons = buttons
        if not self._has_limits():
            buttons.button(
                QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    # ------------------------------------------------------------ helpers
    def _has_limits(self) -> bool:
        limits = getattr(self.data, "bdl_limits", {}) or {}
        return any(df is not None and not df.empty for df in limits.values())

    def _inventory_html(self) -> str:
        """What is flagged, per sheet — so the user knows what will move."""
        masks = getattr(self.data, "bdl_masks", {}) or {}
        limits = getattr(self.data, "bdl_limits", {}) or {}
        if not masks:
            return ("<b>No below-detection values were found</b> in this "
                    "dataset, so there is nothing to reassign.")
        rows = []
        for key, mask in masks.items():
            if mask is None or mask.empty:
                continue
            flagged = int(mask.to_numpy().sum())
            lim = limits.get(key)
            with_limit = 0 if lim is None else int(lim.notna().to_numpy().sum())
            textual = max(flagged - with_limit, 0)
            title = _SHEET_TITLES.get(key, key)
            rows.append(
                f"<li><b>{title}</b> — {flagged} flagged "
                f"({with_limit} with a reported limit, "
                f"{textual} textual)</li>")
        if not rows:
            return ("<b>No below-detection values were found</b> in this "
                    "dataset, so there is nothing to reassign.")
        current = POLICY_LABELS.get(
            getattr(self.data, "bdl_policy", "half"), "—")
        return (f"Currently applied: <b>{current}</b><ul>"
                + "".join(rows) + "</ul>")

    def _apply(self) -> None:
        policy = self.policy_combo.currentData() or "half"
        masks = getattr(self.data, "bdl_masks", {}) or {}
        limits = getattr(self.data, "bdl_limits", {}) or {}
        sheets = {
            "main": "df",
            "isotopes": "isotopes_df",
            "petrography": "petrography_df",
        }
        total = 0
        for key, attr in sheets.items():
            frame = getattr(self.data, attr, None)
            if frame is None or key not in masks:
                continue
            new_df, n = reapply_policy(
                frame, masks.get(key), limits.get(key), policy)
            if n:
                setattr(self.data, attr, new_df)
            total += n
        self.data.bdl_policy = policy
        self.n_changed = total
        self.accept()

    @property
    def policy(self) -> str:
        return self.policy_combo.currentData() or "half"

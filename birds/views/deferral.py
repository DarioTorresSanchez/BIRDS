"""Hold the redraws of views nobody can see.

Every diagram view is a page of the main window's stacked widget, and
much of what happens redraws several of them at once: a session load
restores every view, an Alt-click selection or a new plot style
reaches all of them.  Only the page on screen needs drawing.  A hidden
page now only notes that it is out of date, and the main window draws
it once, when it is shown (``BirdsMainWindow._on_page_shown``).

Restoring the Spider view alone used to redraw it 29 times, once per
element ticked back on, while another page was showing.
"""

from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget

#: Attribute a held view carries until it is drawn.
PENDING = "_redraw_pending"


def defer_while_hidden(view) -> bool:
    """True -- and *view* marked out of date -- when it is a page of a
    stacked widget showing another page; the caller then returns
    without drawing.  False for a page on screen, or a view outside any
    stack (a dialog, a test), which draws as before."""
    stack = view.parentWidget()
    if isinstance(stack, QStackedWidget) and stack.currentWidget() is not view:
        setattr(view, PENDING, True)
        return True
    setattr(view, PENDING, False)
    return False


def draw_if_pending(view) -> bool:
    """Draw *view* if a redraw was held while it was hidden."""
    if not getattr(view, PENDING, False):
        return False
    setattr(view, PENDING, False)
    update = getattr(view, "update_plot", None)
    if callable(update):
        update()
    return True

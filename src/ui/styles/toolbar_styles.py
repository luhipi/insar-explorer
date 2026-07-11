"""Reusable styling helpers for code-created toolbars."""

COMMAND_TOOLBAR_STYLESHEET = """
QToolBar {
    background: transparent;
    margin: 0;
    padding: 0;
    border: none;
    spacing: 1px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 2px;
    margin: 0;
    padding: 1px;
    min-width: 20px;
    min-height: 20px;
}
QToolButton:hover:enabled {
    background: palette(midlight);
    border-color: palette(mid);
}
QToolButton:pressed:enabled {
    background: palette(mid);
    border-color: palette(dark);
}
QToolButton:disabled {
    background: transparent;
    border-color: transparent;
    color: palette(mid);
}
"""


def apply_command_toolbar_style(toolbar):
    """Apply the shared style for code-created command toolbars."""
    toolbar.setStyleSheet(COMMAND_TOOLBAR_STYLESHEET)


def set_toolbar_control_role(widget, role):
    """Assign a reusable visual role to a code-created toolbar control."""
    if role not in {"toggle", "command", "selector"}:
        raise ValueError(f"Unsupported toolbar control role: {role}")
    widget.setProperty("controlRole", role)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()

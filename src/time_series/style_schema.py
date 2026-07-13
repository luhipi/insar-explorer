"""Canonical schema for editable and persisted time-series series styles."""

from collections import OrderedDict

MARKER_OPTIONS = ("o", "s", "^", "v", "+", "x", "d", "*")
LINE_STYLE_OPTIONS = ("", "-", "--", ":", "-.")
FIT_LINE_STYLE_OPTIONS = ("-", "--", ":", "-.")
FIT_LINE_STYLE_DEFAULT = "--"
MARKER_SIZE_RANGE = (0.0, 100.0)
LINE_WIDTH_RANGE = (0.0, 20.0)
FIT_LINE_WIDTH_RANGE = (0.0, 20.0)
FIT_LINE_WIDTH_STEP = 0.5
FIT_LINE_WIDTH_DECIMALS = 1
FIT_LINE_WIDTH_DEFAULT = 2.0
NUMERIC_STEP = 0.5
NUMERIC_DECIMALS = 1

STYLE_PROPERTIES = OrderedDict((
    ("marker_type", "marker"),
    ("marker_color", "marker color"),
    ("marker_size", "marker size"),
    ("marker_edge_color", "marker edge color"),
    ("marker_alpha", "marker alpha"),
    ("line_type", "line style"),
    ("line_color", "line color"),
    ("line_width", "line width"),
    ("line_alpha", "line alpha"),
))

EDITABLE_STYLE_PROPERTIES = OrderedDict((
    ("marker_type", "marker"),
    ("marker_color", "marker color"),
    ("marker_size", "marker size"),
    ("line_type", "line style"),
    ("line_color", "line color"),
    ("line_width", "line width"),
))

PERSISTED_STYLE_KEYS = tuple(STYLE_PROPERTIES.values())
EDITABLE_STYLE_KEYS = tuple(EDITABLE_STYLE_PROPERTIES.values())

RESIDUAL_STYLE_KEYS = (
    "marker", "marker color", "marker size",
    "line style", "line color", "line width",
)


def normalize_color(value, fallback="#000000"):
    """Return a stable JSON-compatible color string without Qt dependencies."""
    if isinstance(value, str):
        value = value.strip()
        if value:
            return value
    return fallback


def normalize_marker(value, fallback="o"):
    """Return a supported marker option."""
    return value if isinstance(value, str) and value in MARKER_OPTIONS else fallback


def normalize_line_style(value, fallback=""):
    """Return a supported Series line-style option."""
    return value if isinstance(value, str) and value in LINE_STYLE_OPTIONS else fallback


def normalize_fit_line_style(value, fallback=FIT_LINE_STYLE_DEFAULT):
    """Return a visible Fit line style, normalizing legacy empty values."""
    return value if isinstance(value, str) and value in FIT_LINE_STYLE_OPTIONS else fallback


def normalize_number(value, limits, fallback):
    """Return a finite float clamped to ``limits``."""
    if isinstance(value, bool):
        return float(fallback)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(fallback)
    if number != number or number in (float("inf"), float("-inf")):
        return float(fallback)
    return max(float(limits[0]), min(float(limits[1]), number))

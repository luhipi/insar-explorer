"""Qt/QGIS enum compatibility helpers for QGIS 3/Qt5 and QGIS 4/Qt6.

Application code should import compatibility constants from this module instead
of branching on Qt binding versions or using enum aliases directly.
"""

try:
    from qgis.PyQt.QtCore import Qt
    try:
        from qgis.PyQt.QtGui import QAction
    except ImportError:
        from qgis.PyQt.QtWidgets import QAction
    from qgis.PyQt.QtWidgets import QColorDialog, QMessageBox, QSizePolicy
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QColorDialog, QMessageBox, QSizePolicy

try:
    from qgis.core import QgsMapLayer, QgsWkbTypes
except ImportError:
    QgsMapLayer = None
    QgsWkbTypes = None


def _enum_value(owner, enum_name, value_name, legacy_name=None):
    """Return a scoped enum value when available, otherwise a legacy alias."""
    enum_owner = getattr(owner, enum_name, None)
    if enum_owner is not None and hasattr(enum_owner, value_name):
        return getattr(enum_owner, value_name)
    return getattr(owner, legacy_name or value_name)


# QtCore.Qt enums
BOTTOM_DOCK_WIDGET_AREA = _enum_value(Qt, "DockWidgetArea", "BottomDockWidgetArea")
ALIGN_RIGHT = _enum_value(Qt, "AlignmentFlag", "AlignRight")
ALIGN_VCENTER = _enum_value(Qt, "AlignmentFlag", "AlignVCenter")
ALIGN_RIGHT_VCENTER = ALIGN_RIGHT | ALIGN_VCENTER
YELLOW = _enum_value(Qt, "GlobalColor", "yellow")
RED = _enum_value(Qt, "GlobalColor", "red")
WAIT_CURSOR = _enum_value(Qt, "CursorShape", "WaitCursor")
LEFT_MOUSE_BUTTON = _enum_value(Qt, "MouseButton", "LeftButton")
RIGHT_MOUSE_BUTTON = _enum_value(Qt, "MouseButton", "RightButton")
ITEM_IS_EDITABLE = _enum_value(Qt, "ItemFlag", "ItemIsEditable")
DASH_LINE = _enum_value(Qt, "PenStyle", "DashLine")
DOT_LINE = _enum_value(Qt, "PenStyle", "DotLine")
DASH_DOT_LINE = _enum_value(Qt, "PenStyle", "DashDotLine")
PEN_STYLE_BY_NAME = {
    "--": DASH_LINE,
    ":": DOT_LINE,
    "-.": DASH_DOT_LINE,
}

# QSizePolicy enums
SIZE_POLICY_EXPANDING = _enum_value(QSizePolicy, "Policy", "Expanding")
SIZE_POLICY_PREFERRED = _enum_value(QSizePolicy, "Policy", "Preferred")

# QMessageBox enums
MESSAGE_ICON_INFORMATION = _enum_value(QMessageBox, "Icon", "Information")
MESSAGE_ICON_CRITICAL = _enum_value(QMessageBox, "Icon", "Critical")
MESSAGE_ICON_WARNING = _enum_value(QMessageBox, "Icon", "Warning")
MESSAGE_BUTTON_OK = _enum_value(QMessageBox, "StandardButton", "Ok")

# QColorDialog enums
DONT_USE_NATIVE_DIALOG = _enum_value(QColorDialog, "ColorDialogOption", "DontUseNativeDialog")

# QGIS enums with scoped/legacy compatibility. These are only available inside QGIS.
POLYGON_GEOMETRY = (
    _enum_value(QgsWkbTypes, "GeometryType", "PolygonGeometry")
    if QgsWkbTypes is not None else None
)
VECTOR_LAYER = (
    _enum_value(QgsMapLayer, "LayerType", "VectorLayer")
    if QgsMapLayer is not None else None
)
RASTER_LAYER = (
    _enum_value(QgsMapLayer, "LayerType", "RasterLayer")
    if QgsMapLayer is not None else None
)


def exec_dialog(dialog):
    """Execute a Qt dialog across PyQt5/PyQt6 bindings."""
    if hasattr(dialog, "exec"):
        return dialog.exec()
    return dialog.exec_()

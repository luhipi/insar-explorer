"""Compact popup editor for time-series marker and line styles."""

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QColor, QIcon

from ...ui_windows.color_picker import ColorPicker
from ...qt_compat import (
    POPUP_WINDOW_FLAG,
    SIZE_POLICY_FIXED,
    SIZE_POLICY_MAXIMUM,
    SIZE_POLICY_PREFERRED,
    configure_compact_command_button,
)

from qgis.PyQt.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CompactColorButton(QPushButton):
    """Square color-preview button matching the former Settings control."""

    colorChanged = pyqtSignal(str)

    def __init__(self, glyph, tooltip, parent=None):
        """Create a fixed-size color preview with its original style glyph."""
        super().__init__(glyph, parent)
        self._color = "#000000"
        self.setToolTip(tooltip)
        self.setFixedSize(24, 24)
        self.setSizePolicy(SIZE_POLICY_FIXED, SIZE_POLICY_FIXED)
        self.clicked.connect(self._pickColor)
        self._updatePreview()

    def setColor(self, color, emit=False):
        """Update the preview immediately and optionally emit the selected color."""
        parsed = QColor(color)
        if not parsed.isValid():
            parsed = QColor("#000000")
        self._color = parsed.name()
        self._updatePreview()
        if emit:
            self.colorChanged.emit(self._color)

    def color(self):
        """Return the current normalized color name."""
        return self._color

    def _updatePreview(self):
        self.setStyleSheet(
            "QPushButton { color: %s; } QPushButton:hover { border: 1px solid #bbb; }"
            % self._color
        )

    def _pickColor(self):
        picker = ColorPicker(self._color, use_native_flag=False, parent=self)
        selected = picker.pickColor()
        if selected != self._color:
            self.setColor(selected, emit=True)


class TimeSeriesStylePopup(QWidget):
    """Non-modal anchored editor for the currently selected time series."""

    markerTypeChanged = pyqtSignal(str)
    markerColorChanged = pyqtSignal(str)
    markerSizeChanged = pyqtSignal(float)
    lineTypeChanged = pyqtSignal(str)
    lineColorChanged = pyqtSignal(str)
    lineWidthChanged = pyqtSignal(float)
    randomizeColorRequested = pyqtSignal()
    setCurrentStyleAsDefaultRequested = pyqtSignal()

    def __init__(self, parent=None):
        """Create compact grouped style controls without applying changes."""
        super().__init__(parent, POPUP_WINDOW_FLAG)
        self.setObjectName("timeSeriesStylePopup")
        self._loading = False

        layout = QVBoxLayout(self)
        self.target_label = QLabel("No active series", self)
        self.target_label.setObjectName("label_ts_style_target")
        layout.addWidget(self.target_label)

        self.marker_group = QGroupBox("Marker", self)
        marker_layout = QFormLayout(self.marker_group)
        self.marker_type = QComboBox(self.marker_group)
        self.marker_type.addItems([".", "o", "s", "^", "v", "+", "x", "d", "*"])
        self.marker_color = CompactColorButton("●", "Select marker color", self.marker_group)
        self.marker_size = QDoubleSpinBox(self.marker_group)
        self.marker_size.setRange(0.0, 100.0)
        self.marker_size.setDecimals(1)
        self.marker_size.setSingleStep(0.5)
        marker_layout.addRow("Type", self.marker_type)
        marker_layout.addRow("Size", self.marker_size)
        marker_layout.addRow("Color", self.marker_color)

        self.line_group = QGroupBox("Line", self)
        line_layout = QFormLayout(self.line_group)
        self.line_type = QComboBox(self.line_group)
        self.line_type.addItems(["", "-", "--", ":", "-."])
        self.line_color = CompactColorButton("━", "Select line color", self.line_group)
        self.line_width = QDoubleSpinBox(self.line_group)
        self.line_width.setRange(0.0, 20.0)
        self.line_width.setDecimals(1)
        self.line_width.setSingleStep(0.5)
        line_layout.addRow("Type", self.line_type)
        line_layout.addRow("Width", self.line_width)
        line_layout.addRow("Color", self.line_color)

        groups_layout = QHBoxLayout()
        groups_layout.setContentsMargins(0, 0, 0, 0)
        groups_layout.addWidget(self.marker_group)
        groups_layout.addWidget(self.line_group)
        layout.addLayout(groups_layout)

        self.randomize_button = QPushButton(self)
        self.randomize_button.setIcon(QIcon(":/icons/icons/plot_random_color.svg"))
        configure_compact_command_button(self.randomize_button)
        self.randomize_button.setToolTip("Randomize marker and line color")
        self.default_button = QPushButton("Set as default", self)
        self.default_button.setToolTip(
            "Use the current series style as the default for newly created time series."
        )
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.addWidget(self.randomize_button)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self.default_button)
        layout.addLayout(actions_layout)

        self.marker_type.currentTextChanged.connect(self._emitMarkerType)
        self.marker_size.valueChanged.connect(self._emitMarkerSize)
        self.line_type.currentTextChanged.connect(self._emitLineType)
        self.line_width.valueChanged.connect(self._emitLineWidth)
        self.marker_color.colorChanged.connect(self.markerColorChanged.emit)
        self.line_color.colorChanged.connect(self.lineColorChanged.emit)
        self.randomize_button.clicked.connect(self.randomizeColorRequested.emit)
        self.default_button.clicked.connect(self.setCurrentStyleAsDefaultRequested.emit)
        for editor in (self.marker_type, self.marker_size, self.line_type, self.line_width):
            editor.setMaximumWidth(110)
        self.marker_group.setSizePolicy(SIZE_POLICY_MAXIMUM, SIZE_POLICY_PREFERRED)
        self.line_group.setSizePolicy(SIZE_POLICY_MAXIMUM, SIZE_POLICY_PREFERRED)
        self.setMaximumWidth(360)
        self.setSelectionState(False)

    def setSelectionState(self, selected, count=0):
        """Update target text and enablement for the current selection."""
        selected = bool(selected)
        if not selected:
            self.target_label.setText("No active series")
        elif int(count) > 1:
            self.target_label.setText(f"Editing: {int(count)} selected series")
        else:
            self.target_label.setText("Editing: Current series")
        for widget in (self.marker_group, self.line_group, self.randomize_button, self.default_button):
            widget.setEnabled(selected)

    def setStyle(self, style):
        """Populate controls from a TimeSeriesStyle without emitting edits."""
        params = style.params.get("time series plot", {}) if style is not None else {}
        self._loading = True
        self.marker_type.setCurrentText(str(params.get("marker", "")))
        self.marker_size.setValue(float(params.get("marker size", 0.0)))
        self.line_type.setCurrentText(str(params.get("line style", "")))
        self.line_width.setValue(float(params.get("line width", 0.0)))
        self.marker_color.setColor(params.get("marker color", "#000000"))
        self.line_color.setColor(params.get("line color", "#000000"))
        self._loading = False

    def setMixedProperties(self, properties):
        """Record property names with mixed values for future multi-selection UI."""
        self.setProperty("mixedStyleProperties", tuple(sorted(properties)))

    def _emitMarkerType(self, value):
        if not self._loading:
            self.markerTypeChanged.emit(value)

    def _emitMarkerSize(self, value):
        if not self._loading:
            self.markerSizeChanged.emit(float(value))

    def _emitLineType(self, value):
        if not self._loading:
            self.lineTypeChanged.emit(value)

    def _emitLineWidth(self, value):
        if not self._loading:
            self.lineWidthChanged.emit(float(value))

"""Compact popup editor for time-series series and fit-line styles."""

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QColor, QIcon

from ...ui_windows.color_picker import ColorPicker
from ...time_series.ensemble_style import (
    ENSEMBLE_MEMBER_WIDTH_RANGE,
    ENSEMBLE_OPACITY_RANGE,
)
from ...time_series.style_schema import (
    FIT_LINE_STYLE_OPTIONS,
    FIT_LINE_WIDTH_DECIMALS,
    FIT_LINE_WIDTH_RANGE,
    FIT_LINE_WIDTH_STEP,
    LINE_STYLE_OPTIONS,
    LINE_WIDTH_RANGE,
    MARKER_OPTIONS,
    MARKER_SIZE_RANGE,
    NUMERIC_DECIMALS,
    NUMERIC_STEP,
    RESIDUAL_LINE_STYLE_OPTIONS,
    RESIDUAL_LINE_WIDTH_RANGE,
    RESIDUAL_MARKER_OPTIONS,
    RESIDUAL_MARKER_SIZE_RANGE,
)
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
    QTabWidget,
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
    fitLineTypeChanged = pyqtSignal(str)
    fitLineColorChanged = pyqtSignal(str)
    fitLineWidthChanged = pyqtSignal(float)
    residualMarkerTypeChanged = pyqtSignal(str)
    residualMarkerColorChanged = pyqtSignal(str)
    residualMarkerSizeChanged = pyqtSignal(float)
    residualLineTypeChanged = pyqtSignal(str)
    residualLineColorChanged = pyqtSignal(str)
    residualLineWidthChanged = pyqtSignal(float)
    randomizeColorRequested = pyqtSignal()
    setCurrentStyleAsDefaultRequested = pyqtSignal()
    setCurrentFitStyleAsDefaultRequested = pyqtSignal()
    randomizeResidualColorRequested = pyqtSignal()
    setCurrentResidualStyleAsDefaultRequested = pyqtSignal()
    ensembleMemberColorChanged = pyqtSignal(str)
    ensembleMemberWidthChanged = pyqtSignal(float)
    ensembleMemberOpacityChanged = pyqtSignal(float)
    ensembleFillColorChanged = pyqtSignal(str)
    ensembleFillOpacityChanged = pyqtSignal(float)
    ensembleSetAsDefaultRequested = pyqtSignal()

    def __init__(self, parent=None):
        """Create compact tabbed style controls without applying changes."""
        super().__init__(parent, POPUP_WINDOW_FLAG)
        self.setObjectName("timeSeriesStylePopup")
        self._loading = False

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("tabs_time_series_style")
        layout.addWidget(self.tabs)
        self._createSeriesTab()
        self._createFitTab()
        self._createResidualTab()
        self._createEnsembleTab()
        self.setMaximumWidth(360)
        self.setSelectionState(False)

    def _createSeriesTab(self):
        """Build the existing Series controls without redesigning them."""
        tab = QWidget(self.tabs)
        layout = QVBoxLayout(tab)
        self.target_label = QLabel("No active series", tab)
        self.target_label.setObjectName("label_ts_style_target")
        layout.addWidget(self.target_label)
        self.series_status_label = QLabel("No active series.", tab)
        self.series_status_label.setToolTip("No active series.")
        self.series_status_label.hide()
        layout.addWidget(self.series_status_label)

        self.marker_group = QGroupBox("Marker", tab)
        marker_layout = QFormLayout(self.marker_group)
        self.marker_type = QComboBox(self.marker_group)
        self.marker_type.addItems(list(MARKER_OPTIONS))
        self.marker_color = CompactColorButton("●", "Select marker color", self.marker_group)
        self.marker_size = QDoubleSpinBox(self.marker_group)
        self.marker_size.setRange(*MARKER_SIZE_RANGE)
        self.marker_size.setDecimals(NUMERIC_DECIMALS)
        self.marker_size.setSingleStep(NUMERIC_STEP)
        marker_layout.addRow("Type", self.marker_type)
        marker_layout.addRow("Size", self.marker_size)
        marker_layout.addRow("Color", self.marker_color)

        self.line_group = QGroupBox("Line", tab)
        line_layout = QFormLayout(self.line_group)
        self.line_type = QComboBox(self.line_group)
        self.line_type.addItems(list(LINE_STYLE_OPTIONS))
        self.line_color = CompactColorButton("━", "Select line color", self.line_group)
        self.line_width = QDoubleSpinBox(self.line_group)
        self.line_width.setRange(*LINE_WIDTH_RANGE)
        self.line_width.setDecimals(NUMERIC_DECIMALS)
        self.line_width.setSingleStep(NUMERIC_STEP)
        line_layout.addRow("Type", self.line_type)
        line_layout.addRow("Width", self.line_width)
        line_layout.addRow("Color", self.line_color)

        groups_layout = QHBoxLayout()
        groups_layout.setContentsMargins(0, 0, 0, 0)
        groups_layout.addWidget(self.marker_group)
        groups_layout.addWidget(self.line_group)
        layout.addLayout(groups_layout)

        self.randomize_button = QPushButton(tab)
        self.randomize_button.setIcon(QIcon(":/icons/icons/plot_random_color.svg"))
        configure_compact_command_button(self.randomize_button)
        self.randomize_button.setToolTip("Randomize marker and line color")
        self.default_button = QPushButton("Set as default", tab)
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
        self.tabs.addTab(tab, "Series")

    def _createFitTab(self):
        """Build fit-line controls from the same compact widgets and schema."""
        tab = QWidget(self.tabs)
        layout = QVBoxLayout(tab)
        self.fit_target_label = QLabel("Editing: Fit line", tab)
        self.fit_target_label.setObjectName("label_fit_style_target")
        layout.addWidget(self.fit_target_label)
        self.fit_status_label = QLabel("Enable Fit in the toolbar to edit its style.", tab)
        self.fit_status_label.setToolTip("Enable Fit in the toolbar to edit its style.")
        self.fit_status_label.hide()
        layout.addWidget(self.fit_status_label)

        self.fit_group = QGroupBox("Fit line", tab)
        fit_layout = QFormLayout(self.fit_group)
        self.fit_line_type = QComboBox(self.fit_group)
        self.fit_line_type.addItems(list(FIT_LINE_STYLE_OPTIONS))
        self.fit_line_color = CompactColorButton("━", "Select fit line color", self.fit_group)
        self.fit_line_width = QDoubleSpinBox(self.fit_group)
        self.fit_line_width.setRange(*FIT_LINE_WIDTH_RANGE)
        self.fit_line_width.setDecimals(FIT_LINE_WIDTH_DECIMALS)
        self.fit_line_width.setSingleStep(FIT_LINE_WIDTH_STEP)
        fit_layout.addRow("Type", self.fit_line_type)
        fit_layout.addRow("Width", self.fit_line_width)
        fit_layout.addRow("Color", self.fit_line_color)
        self.fit_line_type.setMaximumWidth(110)
        self.fit_line_width.setMaximumWidth(110)
        self.fit_group.setSizePolicy(SIZE_POLICY_MAXIMUM, SIZE_POLICY_PREFERRED)
        layout.addWidget(self.fit_group)

        self.fit_default_button = QPushButton("Set as default", tab)
        self.fit_default_button.setToolTip(
            "Use the current fit-line style as the default for newly created time series."
        )
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self.fit_default_button)
        layout.addLayout(actions_layout)
        layout.addStretch(1)

        self.fit_line_type.currentTextChanged.connect(self._emitFitLineType)
        self.fit_line_width.valueChanged.connect(self._emitFitLineWidth)
        self.fit_line_color.colorChanged.connect(self.fitLineColorChanged.emit)
        self.fit_default_button.clicked.connect(self.setCurrentFitStyleAsDefaultRequested.emit)
        self.tabs.addTab(tab, "Fit")

    def _createResidualTab(self):
        """Build residual-series controls by reusing the compact Series widgets."""
        tab = QWidget(self.tabs)
        layout = QVBoxLayout(tab)
        self.residual_target_label = QLabel("Editing: Residual series", tab)
        layout.addWidget(self.residual_target_label)
        self.residual_status_label = QLabel("Enable Residual in the toolbar to edit its style.", tab)
        self.residual_status_label.setToolTip("Enable Residual in the toolbar to edit its style.")
        self.residual_status_label.hide()
        layout.addWidget(self.residual_status_label)
        self.residual_marker_group = QGroupBox("Marker", tab)
        ml = QFormLayout(self.residual_marker_group)
        self.residual_marker_type = QComboBox(self.residual_marker_group)
        self.residual_marker_type.addItems(list(RESIDUAL_MARKER_OPTIONS))
        self.residual_marker_color = CompactColorButton("●", "Select residual marker color", self.residual_marker_group)
        self.residual_marker_size = QDoubleSpinBox(self.residual_marker_group)
        self.residual_marker_size.setRange(*RESIDUAL_MARKER_SIZE_RANGE)
        self.residual_marker_size.setDecimals(NUMERIC_DECIMALS)
        self.residual_marker_size.setSingleStep(NUMERIC_STEP)
        ml.addRow("Type", self.residual_marker_type)
        ml.addRow("Size", self.residual_marker_size)
        ml.addRow("Color", self.residual_marker_color)
        self.residual_line_group = QGroupBox("Line", tab)
        ll = QFormLayout(self.residual_line_group)
        self.residual_line_type = QComboBox(self.residual_line_group)
        self.residual_line_type.addItems(list(RESIDUAL_LINE_STYLE_OPTIONS))
        self.residual_line_color = CompactColorButton("━", "Select residual line color", self.residual_line_group)
        self.residual_line_width = QDoubleSpinBox(self.residual_line_group)
        self.residual_line_width.setRange(*RESIDUAL_LINE_WIDTH_RANGE)
        self.residual_line_width.setDecimals(NUMERIC_DECIMALS)
        self.residual_line_width.setSingleStep(NUMERIC_STEP)
        ll.addRow("Type", self.residual_line_type)
        ll.addRow("Width", self.residual_line_width)
        ll.addRow("Color", self.residual_line_color);
        groups = QHBoxLayout(); groups.setContentsMargins(0,0,0,0)
        groups.addWidget(self.residual_marker_group); groups.addWidget(self.residual_line_group); layout.addLayout(groups)
        self.residual_randomize_button = QPushButton(tab)
        self.residual_randomize_button.setIcon(QIcon(":/icons/icons/plot_random_color.svg"))
        configure_compact_command_button(self.residual_randomize_button)
        self.residual_randomize_button.setToolTip("Randomize residual marker and line color")
        self.residual_default_button = QPushButton("Set as default", tab)
        actions = QHBoxLayout(); actions.addWidget(self.residual_randomize_button); actions.addStretch(1); actions.addWidget(self.residual_default_button); layout.addLayout(actions)
        self.residual_marker_type.currentTextChanged.connect(lambda v: None if self._loading else self.residualMarkerTypeChanged.emit(v))
        self.residual_marker_size.valueChanged.connect(lambda v: None if self._loading else self.residualMarkerSizeChanged.emit(float(v)))
        self.residual_line_type.currentTextChanged.connect(lambda v: None if self._loading else self.residualLineTypeChanged.emit(v))
        self.residual_line_width.valueChanged.connect(lambda v: None if self._loading else self.residualLineWidthChanged.emit(float(v)))
        self.residual_marker_color.colorChanged.connect(self.residualMarkerColorChanged.emit)
        self.residual_line_color.colorChanged.connect(self.residualLineColorChanged.emit)
        self.residual_randomize_button.clicked.connect(self.randomizeResidualColorRequested.emit)
        self.residual_default_button.clicked.connect(self.setCurrentResidualStyleAsDefaultRequested.emit)
        self.tabs.addTab(tab, "Residual")


    def _createEnsembleTab(self):
        """Build compact member-line and spread controls for ensemble snapshots."""
        tab = QWidget(self.tabs)
        layout = QVBoxLayout(tab)
        self.ensemble_target_label = QLabel("No ensemble data", tab)
        self.ensemble_target_label.setObjectName("label_ensemble_style_target")
        layout.addWidget(self.ensemble_target_label)
        self.ensemble_status_label = QLabel("Select multiple points to edit ensemble style.", tab)
        self.ensemble_status_label.setToolTip("Select multiple points to edit ensemble style.")
        self.ensemble_status_label.hide()
        layout.addWidget(self.ensemble_status_label)

        groups = QHBoxLayout()
        groups.setContentsMargins(0, 0, 0, 0)
        self.ensemble_member_group = QGroupBox("Member series", tab)
        member_layout = QFormLayout(self.ensemble_member_group)
        self.ensemble_member_color = CompactColorButton("━", "Select ensemble member color", self.ensemble_member_group)
        self.ensemble_member_width = QDoubleSpinBox(self.ensemble_member_group)
        self.ensemble_member_width.setRange(*ENSEMBLE_MEMBER_WIDTH_RANGE)
        self.ensemble_member_width.setDecimals(NUMERIC_DECIMALS)
        self.ensemble_member_width.setSingleStep(NUMERIC_STEP)
        self.ensemble_member_opacity = QDoubleSpinBox(self.ensemble_member_group)
        self.ensemble_member_opacity.setRange(*ENSEMBLE_OPACITY_RANGE)
        self.ensemble_member_opacity.setDecimals(2)
        self.ensemble_member_opacity.setSingleStep(0.05)
        member_layout.addRow("Color", self.ensemble_member_color)
        member_layout.addRow("Width", self.ensemble_member_width)
        member_layout.addRow("Opacity", self.ensemble_member_opacity)

        self.ensemble_spread_group = QGroupBox("Spread", tab)
        spread_layout = QFormLayout(self.ensemble_spread_group)
        self.ensemble_fill_color = CompactColorButton("■", "Select ensemble spread color", self.ensemble_spread_group)
        self.ensemble_fill_opacity = QDoubleSpinBox(self.ensemble_spread_group)
        self.ensemble_fill_opacity.setRange(*ENSEMBLE_OPACITY_RANGE)
        self.ensemble_fill_opacity.setDecimals(2)
        self.ensemble_fill_opacity.setSingleStep(0.05)
        spread_layout.addRow("Fill color", self.ensemble_fill_color)
        spread_layout.addRow("Opacity", self.ensemble_fill_opacity)
        groups.addWidget(self.ensemble_member_group)
        groups.addWidget(self.ensemble_spread_group)
        layout.addLayout(groups)

        self.ensemble_default_button = QPushButton("Set as default", tab)
        self.ensemble_default_button.setToolTip("Use the current ensemble style as the default for future ensemble plots.")
        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.ensemble_default_button)
        layout.addLayout(actions)
        layout.addStretch(1)

        self.ensemble_member_color.colorChanged.connect(self.ensembleMemberColorChanged.emit)
        self.ensemble_member_width.valueChanged.connect(lambda v: None if self._loading else self.ensembleMemberWidthChanged.emit(float(v)))
        self.ensemble_member_opacity.valueChanged.connect(lambda v: None if self._loading else self.ensembleMemberOpacityChanged.emit(float(v)))
        self.ensemble_fill_color.colorChanged.connect(self.ensembleFillColorChanged.emit)
        self.ensemble_fill_opacity.valueChanged.connect(lambda v: None if self._loading else self.ensembleFillOpacityChanged.emit(float(v)))
        self.ensemble_default_button.clicked.connect(self.ensembleSetAsDefaultRequested.emit)
        for editor in (self.ensemble_member_width, self.ensemble_member_opacity, self.ensemble_fill_opacity):
            editor.setMaximumWidth(90)
        self.tabs.addTab(tab, "Ensemble")

    def setEnsembleStyle(self, ensemble_style):
        """Populate Ensemble controls without emitting user-action signals."""
        self._loading = True
        self.ensemble_member_color.setColor(ensemble_style.member_line_color)
        self.ensemble_member_width.setValue(float(ensemble_style.member_line_width))
        self.ensemble_member_opacity.setValue(float(ensemble_style.member_line_alpha))
        self.ensemble_fill_color.setColor(ensemble_style.fill_color)
        self.ensemble_fill_opacity.setValue(float(ensemble_style.fill_alpha))
        self._loading = False

    def setEnsembleAvailability(self, available, applicable_count=0):
        """Keep the Ensemble tab stable while disabling unavailable controls."""
        available = bool(available)
        if not available:
            text = "No ensemble data"
        elif int(applicable_count) > 1:
            text = f"Editing: {int(applicable_count)} selected series"
        else:
            text = "Editing: Ensemble"
        self.ensemble_target_label.setText(text)
        for widget in (self.ensemble_member_group, self.ensemble_spread_group, self.ensemble_default_button):
            widget.setEnabled(available)

    def setResidualStyle(self, residual_style):
        """Populate Residual controls without emitting edits."""
        self._loading = True
        self.residual_marker_type.setCurrentText(residual_style.marker)
        self.residual_marker_color.setColor(residual_style.marker_color)
        self.residual_marker_size.setValue(float(residual_style.marker_size))
        self.residual_line_type.setCurrentText(residual_style.line_style)
        self.residual_line_color.setColor(residual_style.line_color)
        self.residual_line_width.setValue(float(residual_style.line_width))
        self._loading = False

    @staticmethod
    def _targetText(count, selected_count):
        """Return concise scope text for one style layer."""
        count = int(count)
        selected_count = int(selected_count)
        if count <= 0:
            return "No active series"
        if count == 1 and selected_count == 1:
            return "Editing: Current series"
        if count == selected_count:
            return f"Editing: {count} selected series"
        return f"Editing: {count} applicable series"

    def setLayerAvailability(self, availability):
        """Apply centralized layer availability without emitting edit signals."""
        selected_count = int(availability.selected_count)
        configurations = (
            (
                self.target_label,
                self.series_status_label,
                availability.series_available,
                availability.series_target_count,
                (self.marker_group, self.line_group, self.randomize_button, self.default_button),
            ),
            (
                self.fit_target_label,
                self.fit_status_label,
                availability.fit_available,
                availability.fit_target_count,
                (self.fit_group, self.fit_default_button),
            ),
            (
                self.residual_target_label,
                self.residual_status_label,
                availability.residual_available,
                availability.residual_target_count,
                (self.residual_marker_group, self.residual_line_group,
                 self.residual_randomize_button, self.residual_default_button),
            ),
            (
                self.ensemble_target_label,
                self.ensemble_status_label,
                availability.ensemble_available,
                availability.ensemble_target_count,
                (self.ensemble_member_group, self.ensemble_spread_group,
                 self.ensemble_default_button),
            ),
        )
        for label, status, available, count, widgets in configurations:
            if available:
                label.setText(self._targetText(count, selected_count))
                label.show()
                status.hide()
            else:
                label.hide()
                status.show()
            for widget in widgets:
                widget.setEnabled(bool(available))

    def setSelectionState(self, selected, count=0):
        """Compatibility entry point for Series selection state only."""
        selected = bool(selected)
        if selected:
            self.target_label.setText(self._targetText(int(count), int(count)))
            self.target_label.show()
            self.series_status_label.hide()
        else:
            self.target_label.hide()
            self.series_status_label.show()
        for widget in (self.marker_group, self.line_group, self.randomize_button, self.default_button):
            widget.setEnabled(selected)

    def setStyle(self, style):
        """Populate Series controls from a TimeSeriesStyle without emitting edits."""
        params = style.params.get("time series plot", {}) if style is not None else {}
        self._loading = True
        self.marker_type.setCurrentText(str(params.get("marker", "")))
        self.marker_size.setValue(float(params.get("marker size", 0.0)))
        self.line_type.setCurrentText(str(params.get("line style", "")))
        self.line_width.setValue(float(params.get("line width", 0.0)))
        self.marker_color.setColor(params.get("marker color", "#000000"))
        self.line_color.setColor(params.get("line color", "#000000"))
        self._loading = False

    def setFitStyle(self, fit_style):
        """Populate Fit controls without emitting edits."""
        self._loading = True
        self.fit_line_type.setCurrentText(fit_style.line_style)
        self.fit_line_color.setColor(fit_style.line_color)
        self.fit_line_width.setValue(float(fit_style.line_width))
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

    def _emitFitLineType(self, value):
        if not self._loading:
            self.fitLineTypeChanged.emit(value)

    def _emitFitLineWidth(self, value):
        if not self._loading:
            self.fitLineWidthChanged.emit(float(value))

"""Compact popup for consolidated Replica controls."""

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ...qt_compat import POPUP_WINDOW_FLAG
from ...time_series.replica_schema import (
    REPLICA_INTERVAL_PRESETS,
    replica_interval_for_preset,
    replica_preset_id_for_interval,
)
from ...time_series.style_schema import MARKER_OPTIONS
from .time_series_style_popup import CompactColorButton


class ReplicaPopup(QWidget):
    """Edit all global Replica settings without Apply or Cancel controls."""

    settingsChanged = pyqtSignal(float, int, str, str, float, str, float)
    resetRequested = pyqtSignal()
    CUSTOM_PRESET_ID = "custom"

    def __init__(self, parent=None):
        """Build the compact one-page immediate-update popup."""
        super().__init__(parent, POPUP_WINDOW_FLAG)
        self.setObjectName("replicaPopup")
        self.setWindowTitle("Replica")
        layout = QVBoxLayout(self)
        settings_group = QGroupBox("Settings", self)
        settings_form = QFormLayout(settings_group)
        self.preset_combo = QComboBox(self)
        self.preset_combo.setEditable(False)
        self.preset_combo.setToolTip("Select a common radar half-wavelength interval.")
        settings_control_width = 140
        for preset_id, label, _interval in REPLICA_INTERVAL_PRESETS:
            self.preset_combo.addItem(label, preset_id)
        self.preset_combo.addItem("Custom", self.CUSTOM_PRESET_ID)
        self.interval_spin = QDoubleSpinBox(self)
        self.interval_spin.setRange(0.1, 10000.0)
        self.interval_spin.setDecimals(1)
        self.interval_spin.setSuffix(" mm")
        self.preset_combo.setFixedWidth(settings_control_width)
        self.interval_spin.setFixedWidth(settings_control_width)
        self.pair_count_spin = QSpinBox(self)
        self.pair_count_spin.setRange(1, 10)
        self.pair_count_spin.setFixedWidth(settings_control_width)
        settings_form.addRow("Preset", self.preset_combo)
        settings_form.addRow("Interval", self.interval_spin)
        settings_form.addRow("Pairs", self.pair_count_spin)
        layout.addWidget(settings_group)
        layout.addSpacing(3)

        appearance_group = QGroupBox("Appearance", self)
        appearance_form = QFormLayout(appearance_group)
        self.color_1_button = CompactColorButton(
            "●", "First color used by the alternating Replica pattern.", self
        )
        self.color_2_button = CompactColorButton(
            "●", "Second color used by the alternating Replica pattern.", self
        )
        self.opacity_spin = QSpinBox(self)
        self.opacity_spin.setRange(0, 100)
        self.opacity_spin.setSingleStep(5)
        self.opacity_spin.setSuffix(" %")
        appearance_control_width = 110
        self.opacity_spin.setFixedWidth(appearance_control_width)
        self.marker_combo = QComboBox(self)
        self.marker_combo.setToolTip("Replica marker")
        for marker in MARKER_OPTIONS:
            self.marker_combo.addItem(marker, marker)
        self.marker_combo.setFixedWidth(appearance_control_width)
        self.marker_size_spin = QDoubleSpinBox(self)
        self.marker_size_spin.setRange(0.0, 100.0)
        self.marker_size_spin.setSingleStep(0.5)
        self.marker_size_spin.setDecimals(1)
        self.marker_size_spin.setFixedWidth(appearance_control_width)
        self.color_1_button.setAccessibleName("Replica Color 1")
        self.color_2_button.setAccessibleName("Replica Color 2")
        colors_widget = QWidget(self)
        colors_layout = QGridLayout(colors_widget)
        colors_layout.setContentsMargins(0, 0, 0, 0)
        colors_layout.setHorizontalSpacing(6)
        colors_layout.setVerticalSpacing(0)
        colors_layout.addWidget(QLabel("Color 1", colors_widget), 0, 0)
        colors_layout.addWidget(self.color_1_button, 0, 1)
        colors_layout.setColumnMinimumWidth(2, 8)
        colors_layout.addWidget(QLabel("Color 2", colors_widget), 0, 3)
        colors_layout.addWidget(self.color_2_button, 0, 4)
        colors_layout.setColumnStretch(5, 1)
        appearance_form.addRow(colors_widget)
        appearance_form.addRow("Opacity", self.opacity_spin)
        appearance_form.addRow("Marker", self.marker_combo)
        appearance_form.addRow("Marker size", self.marker_size_spin)
        layout.addWidget(appearance_group)

        self.reset_button = QPushButton("Reset settings", self)
        layout.addWidget(self.reset_button)
        QWidget.setTabOrder(self.color_1_button, self.color_2_button)
        QWidget.setTabOrder(self.color_2_button, self.opacity_spin)
        QWidget.setTabOrder(self.opacity_spin, self.marker_combo)
        QWidget.setTabOrder(self.marker_combo, self.marker_size_spin)
        self.preset_combo.currentIndexChanged.connect(self._presetChanged)
        self.interval_spin.valueChanged.connect(self._intervalChanged)
        self.pair_count_spin.valueChanged.connect(self._emitSettings)
        self.color_1_button.colorChanged.connect(self._emitSettings)
        self.color_2_button.colorChanged.connect(self._emitSettings)
        self.opacity_spin.valueChanged.connect(self._emitSettings)
        self.marker_combo.currentIndexChanged.connect(self._emitSettings)
        self.marker_size_spin.valueChanged.connect(self._emitSettings)
        self.reset_button.clicked.connect(self.resetRequested.emit)

    def _setPresetForInterval(self, interval_mm):
        """Synchronize the preset view from the authoritative numeric interval."""
        preset_id = replica_preset_id_for_interval(interval_mm) or self.CUSTOM_PRESET_ID
        previous = self.preset_combo.blockSignals(True)
        try:
            index = self.preset_combo.findData(preset_id)
            self.preset_combo.setCurrentIndex(max(0, index))
        finally:
            self.preset_combo.blockSignals(previous)

    def _presetChanged(self, _index):
        """Apply a named preset to Interval and emit one consolidated update."""
        interval = replica_interval_for_preset(self.preset_combo.currentData())
        if interval is None:
            return
        previous = self.interval_spin.blockSignals(True)
        try:
            self.interval_spin.setValue(interval)
        finally:
            self.interval_spin.blockSignals(previous)
        self._emitSettings()

    def _intervalChanged(self, interval_mm):
        """Derive the preset selection from a manually edited interval."""
        self._setPresetForInterval(interval_mm)
        self._emitSettings()

    def _emitSettings(self, *_args):
        """Emit normalized UI values, converting percent opacity at the boundary."""
        self.settingsChanged.emit(
            self.interval_spin.value(), self.pair_count_spin.value(),
            self.color_1_button.color(),
            self.color_2_button.color(), self.opacity_spin.value() / 100.0,
            self.marker_combo.currentData(), self.marker_size_spin.value(),
        )

    def setSettings(self, settings):
        """Refresh controls from runtime state without emitting writes."""
        controls = (
            self.preset_combo, self.interval_spin,
            self.pair_count_spin, self.color_1_button, self.color_2_button,
            self.opacity_spin, self.marker_combo, self.marker_size_spin,
        )
        previous = [control.blockSignals(True) for control in controls]
        try:
            self.interval_spin.setValue(settings.interval_mm)
            preset_id = replica_preset_id_for_interval(settings.interval_mm) or self.CUSTOM_PRESET_ID
            self.preset_combo.setCurrentIndex(max(0, self.preset_combo.findData(preset_id)))
            self.pair_count_spin.setValue(settings.pair_count)
            self.color_1_button.setColor(settings.color_1)
            self.color_2_button.setColor(settings.color_2)
            self.opacity_spin.setValue(round(settings.opacity * 100))
            index = self.marker_combo.findData(settings.marker)
            self.marker_combo.setCurrentIndex(max(0, index))
            self.marker_size_spin.setValue(settings.marker_size)
        finally:
            for control, blocked in zip(controls, previous):
                control.blockSignals(blocked)

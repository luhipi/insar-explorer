"""Compact popup for persistent plot-export defaults."""

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QWidget,
)


class ExportSettingsPopup(QWidget):
    """Edit persistent export defaults with immediate commit semantics."""

    settingsChanged = pyqtSignal(str, float, str)
    resetRequested = pyqtSignal()

    DPI_OPTIONS = ("72", "150", "300", "600", "1200")

    def __init__(self, parent=None):
        """Build the compact settings popup."""
        super().__init__(parent)
        self.setObjectName("exportSettingsPopup")
        self.setWindowTitle("Export settings")
        window_type = getattr(__import__('qgis.PyQt.QtCore', fromlist=['Qt']).Qt, 'WindowType', __import__('qgis.PyQt.QtCore', fromlist=['Qt']).Qt)
        self.setWindowFlags(window_type.Popup)

        layout = QVBoxLayout(self)
        title = QLabel("Export settings", self)
        title.setObjectName("label_export_settings_title")
        layout.addWidget(title)

        form = QFormLayout()
        self.resolution_combo = QComboBox(self)
        self.resolution_combo.setObjectName("combo_export_resolution")
        for dpi in self.DPI_OPTIONS:
            self.resolution_combo.addItem(f"{dpi} dpi", dpi)
        self.resolution_combo.setMaximumWidth(120)

        self.aspect_ratio_spin = QDoubleSpinBox(self)
        self.aspect_ratio_spin.setObjectName("spin_export_aspect_ratio")
        self.aspect_ratio_spin.setRange(1.0, 10.0)
        self.aspect_ratio_spin.setDecimals(1)
        self.aspect_ratio_spin.setSingleStep(1.0)
        self.aspect_ratio_spin.setMaximumWidth(90)
        self.aspect_ratio_spin.setToolTip(
            "Controls the width-to-height ratio of the exported plot area."
        )

        self.credit_edit = QLineEdit(self)
        self.credit_edit.setObjectName("edit_export_credit")
        self.credit_edit.setMaximumWidth(260)
        self.credit_edit.setToolTip("Leave empty to omit export credit.")

        form.addRow("Resolution", self.resolution_combo)
        form.addRow("Aspect ratio", self.aspect_ratio_spin)
        form.addRow("Credit", self.credit_edit)
        layout.addLayout(form)

        actions = QHBoxLayout()
        self.reset_button = QPushButton("Reset defaults", self)
        self.reset_button.setObjectName("button_export_reset_defaults")
        actions.addWidget(self.reset_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.resolution_combo.currentIndexChanged.connect(self._emitSettings)
        self.aspect_ratio_spin.valueChanged.connect(self._emitSettings)
        self.credit_edit.textChanged.connect(self._emitSettings)
        self.reset_button.clicked.connect(self.resetRequested.emit)

    def settings(self):
        """Return the normalized values currently displayed by the popup."""
        dpi = self.resolution_combo.currentData() or "300"
        return str(dpi), float(self.aspect_ratio_spin.value()), self.credit_edit.text()

    def setSettings(self, settings):
        """Refresh controls without emitting persistence writes."""
        widgets = (self.resolution_combo, self.aspect_ratio_spin, self.credit_edit)
        previous = [widget.blockSignals(True) for widget in widgets]
        try:
            index = self.resolution_combo.findData(str(settings.dpi))
            self.resolution_combo.setCurrentIndex(max(0, index))
            self.aspect_ratio_spin.setValue(float(settings.aspect_ratio))
            self.credit_edit.setText(settings.credit)
        finally:
            for widget, blocked in zip(widgets, previous):
                widget.blockSignals(blocked)

    def _emitSettings(self, *_args):
        """Emit one complete settings value after a user edit."""
        self.settingsChanged.emit(*self.settings())

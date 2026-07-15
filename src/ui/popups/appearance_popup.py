"""Compact popup for persistent time-series plot appearance."""

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from .time_series_style_popup import CompactColorButton


class AppearancePopup(QWidget):
    """Edit plot appearance with immediate commit semantics."""

    settingsChanged = pyqtSignal(str, str, str, int, str, str)
    resetRequested = pyqtSignal()

    GRID_MODES = (
        ("Both", "both"),
        ("Horizontal", "horizontal"),
        ("Vertical", "vertical"),
        ("None", "none"),
    )

    DATE_FORMATS = (
        ("YYYY-MM-DD", "%Y-%m-%d"),
        ("DD/MM/YYYY", "%d/%m/%Y"),
        ("MM/DD/YYYY", "%m/%d/%Y"),
        ("DD Mon YYYY", "%d %b %Y"),
        ("Mon YYYY", "%b %Y"),
        ("YYYY", "%Y"),
    )

    def __init__(self, parent=None):
        """Build the popup without Apply or Cancel controls."""
        super().__init__(parent)
        self.setObjectName("appearancePopup")
        self.setWindowTitle("Appearance")
        qt = __import__('qgis.PyQt.QtCore', fromlist=['Qt']).Qt
        self.setWindowFlags(getattr(qt, 'WindowType', qt).Popup)

        layout = QVBoxLayout(self)
        self.time_series_title_edit = QLineEdit(self)
        self.residual_title_edit = QLineEdit(self)
        titles = QGroupBox("Titles", self)
        title_form = QFormLayout(titles)
        title_form.addRow("Time series title", self.time_series_title_edit)
        title_form.addRow("Residual title", self.residual_title_edit)
        layout.addWidget(titles)

        self.date_format_combo = QComboBox(self)
        for label, value in self.DATE_FORMATS:
            self.date_format_combo.addItem(label, value)
        self.date_format_combo.setEditable(True)
        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(1, 200)
        axes = QGroupBox("Axes", self)
        axes_form = QFormLayout(axes)
        axes_form.addRow("Date format", self.date_format_combo)
        axes_form.addRow("Font size", self.font_size_spin)
        layout.addWidget(axes)

        self.background_color_button = CompactColorButton(
            "■", "Select plot background color", self
        )
        self.grid_mode_combo = QComboBox(self)
        self.grid_mode_combo.setEditable(False)
        self.grid_mode_combo.setMaximumWidth(140)
        for label, value in self.GRID_MODES:
            self.grid_mode_combo.addItem(label, value)
        background = QGroupBox("Background", self)
        background_form = QFormLayout(background)
        background_form.addRow("Background color", self.background_color_button)
        background_form.addRow("Grid", self.grid_mode_combo)
        layout.addWidget(background)

        actions = QHBoxLayout()
        self.reset_button = QPushButton("Reset defaults", self)
        actions.addWidget(self.reset_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.time_series_title_edit.textChanged.connect(self._emitSettings)
        self.residual_title_edit.textChanged.connect(self._emitSettings)
        self.date_format_combo.currentTextChanged.connect(self._emitSettings)
        self.font_size_spin.valueChanged.connect(self._emitSettings)
        self.background_color_button.colorChanged.connect(self._emitSettings)
        self.grid_mode_combo.currentIndexChanged.connect(self._emitSettings)
        self.reset_button.clicked.connect(self.resetRequested.emit)

    def settings(self):
        """Return the complete appearance value currently displayed."""
        date_format = self.date_format_combo.currentData()
        if self.date_format_combo.isEditable() and self.date_format_combo.currentText() not in [
            self.date_format_combo.itemText(i) for i in range(self.date_format_combo.count())
        ]:
            date_format = self.date_format_combo.currentText()
        return (
            self.time_series_title_edit.text(),
            self.residual_title_edit.text(),
            str(date_format or "%Y-%m-%d"),
            int(self.font_size_spin.value()),
            self.background_color_button.color(),
            str(self.grid_mode_combo.currentData() or "both"),
        )

    def setSettings(self, settings):
        """Refresh all controls without emitting persistence writes."""
        widgets = (self.time_series_title_edit, self.residual_title_edit,
                   self.date_format_combo, self.font_size_spin,
                   self.background_color_button, self.grid_mode_combo)
        previous = [widget.blockSignals(True) for widget in widgets]
        try:
            self.time_series_title_edit.setText(settings.time_series_title)
            self.residual_title_edit.setText(settings.residual_title)
            index = self.date_format_combo.findData(settings.date_format)
            if index >= 0:
                self.date_format_combo.setCurrentIndex(index)
            else:
                self.date_format_combo.setEditText(settings.date_format or "%Y-%m-%d")
            self.font_size_spin.setValue(int(settings.font_size))
            self.background_color_button.setColor(settings.plot_background)
            grid_index = self.grid_mode_combo.findData(settings.grid_mode)
            self.grid_mode_combo.setCurrentIndex(grid_index if grid_index >= 0 else 0)
        finally:
            for widget, blocked in zip(widgets, previous):
                widget.blockSignals(blocked)

    def _emitSettings(self, *_args):
        """Emit one complete immutable replacement after a user edit."""
        self.settingsChanged.emit(*self.settings())

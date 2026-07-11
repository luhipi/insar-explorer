"""Toolbar actions for the time-series plot panel."""

from qgis.PyQt.QtCore import QSize, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QSizePolicy, QToolBar, QWidget


class TimeSeriesToolbar(QToolBar):
    """Code-defined toolbar exposing semantic time-series action signals."""

    settingsRequested = pyqtSignal()
    plotExportRequested = pyqtSignal()
    dataExportRequested = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the toolbar and its actions."""
        super().__init__(parent)
        self.setObjectName("time_series_toolbar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(20, 20))

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        self.settings_action = QAction(QIcon(":/icons/icons/setting.svg"), "Settings", self)
        self.settings_action.setToolTip("Open time-series settings")
        self.plot_export_action = QAction(QIcon(":/icons/icons/screenshot.svg"), "Save plot", self)
        self.plot_export_action.setToolTip("Save the time-series plot")
        self.data_export_action = QAction(QIcon(":/icons/icons/export.svg"), "Export values", self)
        self.data_export_action.setToolTip("Export time-series values")

        self.addAction(self.settings_action)
        self.addAction(self.plot_export_action)
        self.addAction(self.data_export_action)

        self.settings_action.triggered.connect(self.settingsRequested.emit)
        self.plot_export_action.triggered.connect(self.plotExportRequested.emit)
        self.data_export_action.triggered.connect(self.dataExportRequested.emit)

    def setPlotExportEnabled(self, enabled):
        """Enable or disable plot export without inspecting application state."""
        self.plot_export_action.setEnabled(enabled)

    def setDataExportEnabled(self, enabled):
        """Enable or disable data export without inspecting application state."""
        self.data_export_action.setEnabled(enabled)

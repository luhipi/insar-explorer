"""Toolbar actions for the time-series plot panel."""

from qgis.PyQt.QtCore import QSize, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QToolBar, QToolButton, QWidget

from ...qt_compat import (
    QAction,
    QActionGroup,
    SIZE_POLICY_EXPANDING,
    SIZE_POLICY_PREFERRED,
    TOOL_BUTTON_INSTANT_POPUP,
)
from ..styles import apply_command_toolbar_style, set_toolbar_control_role


class TimeSeriesToolbar(QToolBar):
    """Code-defined toolbar exposing semantic time-series action signals."""

    settingsRequested = pyqtSignal()
    plotExportRequested = pyqtSignal()
    dataExportRequested = pyqtSignal()
    fitEnabledChanged = pyqtSignal(bool)
    fitModelChanged = pyqtSignal(str)
    seasonalEnabledChanged = pyqtSignal(bool)
    residualEnabledChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        """Initialize the toolbar and its actions."""
        super().__init__(parent)
        self.setObjectName("timeSeriesToolbar")
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(18, 18))
        self.setContentsMargins(0, 0, 0, 0)
        apply_command_toolbar_style(self)

        self.fit_enabled_action = self._createToggleAction(
            ":/icons/icons/fit_curve.svg",
            "Fit",
            "Toggle time-series fitting",
            "action_ts_fit_enabled",
        )
        self.addAction(self.fit_enabled_action)

        self.fit_model_button = QToolButton(self)
        self.fit_model_button.setObjectName("tool_ts_fit_model")
        set_toolbar_control_role(self.fit_model_button, "selector")
        self.fit_model_button.setPopupMode(TOOL_BUTTON_INSTANT_POPUP)
        self.fit_model_menu = QMenu(self.fit_model_button)
        self.fit_model_menu.setObjectName("menu_ts_fit_model")
        self.fit_model_group = QActionGroup(self.fit_model_menu)
        self.fit_model_group.setExclusive(True)
        self.fit_model_actions = {}
        for model, text, icon_path, object_name in (
            ("poly-1", "Linear", ":/icons/icons/fit_poly1.svg", "action_ts_fit_linear"),
            ("poly-2", "Second order", ":/icons/icons/fit_poly2.svg", "action_ts_fit_second_order"),
            ("poly-3", "Third order", ":/icons/icons/fit_poly3.svg", "action_ts_fit_third_order"),
            ("exp", "Exponential", ":/icons/icons/fit_exponential.svg", "action_ts_fit_exponential"),
        ):
            action = QAction(QIcon(icon_path), text, self.fit_model_group)
            action.setObjectName(object_name)
            action.setCheckable(True)
            action.setData(model)
            self.fit_model_group.addAction(action)
            self.fit_model_menu.addAction(action)
            self.fit_model_actions[model] = action
        self.fit_model_actions["poly-1"].setChecked(True)
        self.fit_model_button.setMenu(self.fit_model_menu)
        self.fit_model_button.setDefaultAction(self.fit_model_actions["poly-1"])
        self.addWidget(self.fit_model_button)
        self._updateFitToggleMetadata()

        self.seasonal_action = self._createToggleAction(
            ":/icons/icons/fit__add_seasonal.svg",
            "Seasonal",
            "Include a seasonal component in the fitted model",
            "action_ts_fit_seasonal",
        )
        self.addAction(self.seasonal_action)
        self.addSeparator()
        self.residual_action = self._createToggleAction(
            ":/icons/icons/residual.svg",
            "Residual",
            "Show residual values for the fitted model",
            "action_ts_show_residual",
        )
        self.addAction(self.residual_action)

        spacer = QWidget(self)
        spacer.setObjectName("timeSeriesToolbarSpacer")
        spacer.setSizePolicy(
            SIZE_POLICY_EXPANDING,
            SIZE_POLICY_PREFERRED,
        )
        self.addWidget(spacer)

        self.settings_action = self._createAction(
            ":/icons/icons/setting.svg",
            "Time-series settings",
            "Configure time-series plot settings",
            "action_ts_settings",
        )
        self.plot_export_action = self._createAction(
            ":/icons/icons/screenshot.svg",
            "Export plot",
            "Export the current time-series plot",
            "action_ts_export_plot",
        )
        self.data_export_action = self._createAction(
            ":/icons/icons/export.svg",
            "Export data",
            "Export the current time-series data",
            "action_ts_export_data",
        )

        self.addAction(self.settings_action)
        self.addSeparator()
        self.addAction(self.plot_export_action)
        self.addAction(self.data_export_action)

        for action in (
            self.fit_enabled_action,
            self.seasonal_action,
            self.residual_action,
        ):
            self._setActionControlRole(action, "toggle")
        for action in (
            self.settings_action,
            self.plot_export_action,
            self.data_export_action,
        ):
            self._setActionControlRole(action, "command")

        self.settings_action.triggered.connect(self.settingsRequested.emit)
        self.plot_export_action.triggered.connect(self.plotExportRequested.emit)
        self.data_export_action.triggered.connect(self.dataExportRequested.emit)
        self.fit_enabled_action.toggled.connect(self.fitEnabledChanged.emit)
        self.fit_model_group.triggered.connect(
            lambda action: self.fitModelChanged.emit(action.data())
        )
        self.seasonal_action.toggled.connect(self.seasonalEnabledChanged.emit)
        self.residual_action.toggled.connect(self.residualEnabledChanged.emit)


    def setFitEnabled(self, enabled):
        """Update the fit toggle without emitting a user-change signal."""
        previous = self.fit_enabled_action.blockSignals(True)
        self.fit_enabled_action.setChecked(bool(enabled))
        self.fit_enabled_action.blockSignals(previous)

    def setSelectedFitModel(self, model):
        """Update the selected menu model without emitting a user-change signal."""
        action = self.fit_model_actions[model]
        previous = self.fit_model_group.blockSignals(True)
        action.setChecked(True)
        self.fit_model_button.setDefaultAction(action)
        self.fit_model_group.blockSignals(previous)
        self._updateFitToggleMetadata()


    def _updateFitToggleMetadata(self):
        """Update Fit metadata for the currently selected model."""
        selected_action = next(
            action for action in self.fit_model_actions.values() if action.isChecked()
        )
        model_name = selected_action.text()
        self.fit_enabled_action.setToolTip(f"Toggle fit using {model_name}")
        self.fit_enabled_action.setStatusTip(f"Fit using {model_name} model")
        self.fit_enabled_action.setWhatsThis(f"Fit using {model_name} model")
        self.fit_model_button.setAccessibleName(f"Selected fit model: {model_name}")

    def setSeasonalEnabled(self, enabled):
        """Update the seasonal toggle without emitting a user-change signal."""
        previous = self.seasonal_action.blockSignals(True)
        self.seasonal_action.setChecked(bool(enabled))
        self.seasonal_action.blockSignals(previous)

    def setResidualEnabled(self, enabled):
        """Update the residual toggle without emitting a user-change signal."""
        previous = self.residual_action.blockSignals(True)
        self.residual_action.setChecked(bool(enabled))
        self.residual_action.blockSignals(previous)

    def _setActionControlRole(self, action, role):
        """Assign a semantic role to the tool button generated for an action."""
        button = self.widgetForAction(action)
        if isinstance(button, QToolButton):
            set_toolbar_control_role(button, role)

    def _createAction(self, icon_path, text, tooltip, object_name):
        """Create a non-checkable command action with stable metadata."""
        action = QAction(QIcon(icon_path), text, self)
        action.setObjectName(object_name)
        action.setToolTip(tooltip)
        action.setCheckable(False)
        return action

    def _createToggleAction(self, icon_path, text, tooltip, object_name):
        """Create a checkable toolbar action for an independent state toggle."""
        action = QAction(QIcon(icon_path), text, self)
        action.setObjectName(object_name)
        action.setToolTip(tooltip)
        action.setCheckable(True)
        return action

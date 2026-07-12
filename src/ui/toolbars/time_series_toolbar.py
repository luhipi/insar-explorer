"""Toolbar actions for the time-series plot panel."""

from qgis.PyQt.QtCore import QSize, Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QInputDialog,
    QMenu,
    QToolBar,
    QToolButton,
    QWidget,
)

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
    yAxisModeChanged = pyqtSignal(str)
    replicaEnabledChanged = pyqtSignal(bool)
    replicaIntervalChanged = pyqtSignal(float)

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
        self.fit_model_button.setCheckable(False)
        self._updateFitModelSelector(self.fit_model_actions["poly-1"])
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

        self.y_axis_button = QToolButton(self)
        self.y_axis_button.setObjectName("tool_ts_y_axis")
        set_toolbar_control_role(self.y_axis_button, "selector")
        self.y_axis_button.setPopupMode(TOOL_BUTTON_INSTANT_POPUP)
        self.y_axis_menu = QMenu(self.y_axis_button)
        self.y_axis_menu.setObjectName("menu_ts_y_axis")
        self.y_axis_group = QActionGroup(self.y_axis_menu)
        self.y_axis_group.setExclusive(True)
        self.y_axis_actions = {}
        for mode, text, tooltip, icon_path, object_name in (
            (
                "from_data",
                "From data",
                "Y-axis from data",
                ":/icons/icons/y_axis_from_data.svg",
                "action_ts_y_from_data",
            ),
            (
                "symmetric",
                "Symmetric",
                "Symmetric Y-axis",
                ":/icons/icons/y_axis_symmetric.svg",
                "action_ts_y_symmetric",
            ),
            (
                "adaptive",
                "Adaptive",
                "Adaptive Y-axis",
                ":/icons/icons/y_axis_adaptive.svg",
                "action_ts_y_adaptive",
            ),
        ):
            action = QAction(QIcon(icon_path), text, self.y_axis_group)
            action.setObjectName(object_name)
            action.setCheckable(True)
            action.setData(mode)
            action.setToolTip(tooltip)
            self.y_axis_group.addAction(action)
            self.y_axis_menu.addAction(action)
            self.y_axis_actions[mode] = action
        self.y_axis_actions["from_data"].setChecked(True)
        self.y_axis_button.setMenu(self.y_axis_menu)
        self.y_axis_button.setCheckable(False)
        self._updateYAxisSelector(self.y_axis_actions["from_data"])
        self.addWidget(self.y_axis_button)

        self.addSeparator()
        self.replica_enabled_action = self._createToggleAction(
            ":/icons/icons/replica.svg",
            "Replica",
            "Toggle time-series replicas",
            "action_ts_replica_enabled",
        )
        self.addAction(self.replica_enabled_action)

        self.replica_interval_button = QToolButton(self)
        self.replica_interval_button.setObjectName("tool_ts_replica_interval")
        set_toolbar_control_role(self.replica_interval_button, "selector")
        self.replica_interval_button.setPopupMode(TOOL_BUTTON_INSTANT_POPUP)
        tool_button_style = getattr(Qt, "ToolButtonStyle", Qt)
        self.replica_interval_button.setToolButtonStyle(
            tool_button_style.ToolButtonTextOnly
        )
        self.replica_interval_menu = QMenu(self.replica_interval_button)
        self.replica_interval_menu.setObjectName("menu_ts_replica_interval")
        self.replica_interval_group = QActionGroup(self.replica_interval_menu)
        self.replica_interval_group.setExclusive(True)
        self.replica_interval_actions = {}
        for preset_id, text, interval_mm, object_name in (
            ("s1", "Sentinel-1 (C-band) — 27.8 mm", 27.8, "action_replica_s1"),
            ("tsx", "TerraSAR-X (X-band) — 15.5 mm", 15.5, "action_replica_tsx"),
            ("alos", "ALOS (L-band) — 118.0 mm", 118.0, "action_replica_alos"),
            ("nisar_l", "NISAR (L-band) — 120.0 mm", 120.0, "action_replica_nisar_l"),
        ):
            action = QAction(text, self.replica_interval_group)
            action.setObjectName(object_name)
            action.setCheckable(True)
            action.setData(interval_mm)
            action.setProperty("presetId", preset_id)
            self.replica_interval_group.addAction(action)
            self.replica_interval_menu.addAction(action)
            self.replica_interval_actions[preset_id] = action
        self.replica_interval_menu.addSeparator()
        self.replica_custom_action = QAction("Custom…", self.replica_interval_group)
        self.replica_custom_action.setObjectName("action_replica_custom")
        self.replica_custom_action.setCheckable(True)
        self.replica_custom_action.setData(None)
        self.replica_interval_group.addAction(self.replica_custom_action)
        self.replica_interval_menu.addAction(self.replica_custom_action)
        self.replica_interval_actions["custom"] = self.replica_custom_action
        self.replica_interval_button.setMenu(self.replica_interval_menu)
        self.replica_interval_button.setCheckable(False)
        self._replica_interval_mm = 27.8
        self.setReplicaInterval(27.8)
        self.addWidget(self.replica_interval_button)

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
            self.replica_enabled_action,
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
        self.fit_model_group.triggered.connect(self._fitModelActionTriggered)
        self.seasonal_action.toggled.connect(self.seasonalEnabledChanged.emit)
        self.residual_action.toggled.connect(self.residualEnabledChanged.emit)
        self.y_axis_group.triggered.connect(self._yAxisActionTriggered)
        self.replica_enabled_action.toggled.connect(self.replicaEnabledChanged.emit)
        self.replica_interval_group.triggered.connect(self._replicaIntervalActionTriggered)

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
        self.fit_model_group.blockSignals(previous)
        self._updateFitModelSelector(action)
        self._updateFitToggleMetadata()

    def _fitModelActionTriggered(self, action):
        """Update selector presentation and emit the selected model identifier."""
        self._updateFitModelSelector(action)
        self._updateFitToggleMetadata()
        self.fitModelChanged.emit(action.data())

    def _updateFitModelSelector(self, action):
        """Render the selected model without inheriting its checked action state."""
        self.fit_model_button.setIcon(action.icon())
        self.fit_model_button.setText(action.text())
        self.fit_model_button.setToolTip(action.text())
        self.fit_model_button.setStatusTip(action.statusTip())
        self.fit_model_button.setWhatsThis(action.whatsThis())

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

    def setSelectedYAxisMode(self, mode):
        """Update the selected Y-axis mode without emitting a user-change signal."""
        action = self.y_axis_actions[mode]
        previous = self.y_axis_group.blockSignals(True)
        action.setChecked(True)
        self.y_axis_group.blockSignals(previous)
        self._updateYAxisSelector(action)

    def _yAxisActionTriggered(self, action):
        """Update selector presentation and emit the selected Y-axis mode."""
        self._updateYAxisSelector(action)
        self.yAxisModeChanged.emit(action.data())

    def _updateYAxisSelector(self, action):
        """Render the current Y-axis mode without a checked toolbar state."""
        self.y_axis_button.setIcon(action.icon())
        self.y_axis_button.setText(action.text())
        self.y_axis_button.setToolTip(action.toolTip())
        self.y_axis_button.setStatusTip(action.toolTip())
        self.y_axis_button.setWhatsThis(action.toolTip())
        self.y_axis_button.setAccessibleName(f"Selected Y-axis mode: {action.text()}")

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

    def setReplicaEnabled(self, enabled):
        """Update the Replica toggle without emitting a user-change signal."""
        previous = self.replica_enabled_action.blockSignals(True)
        self.replica_enabled_action.setChecked(bool(enabled))
        self.replica_enabled_action.blockSignals(previous)

    def setReplicaInterval(self, interval_mm):
        """Render a preset or custom replica interval without emitting a signal."""
        interval_mm = float(interval_mm)
        self._replica_interval_mm = interval_mm
        matched_action = None
        for preset_id, action in self.replica_interval_actions.items():
            if preset_id != "custom" and abs(float(action.data()) - interval_mm) < 0.05:
                matched_action = action
                break
        action = matched_action or self.replica_custom_action
        previous = self.replica_interval_group.blockSignals(True)
        action.setChecked(True)
        self.replica_interval_group.blockSignals(previous)
        self._updateReplicaIntervalSelector(action, interval_mm)

    def _replicaIntervalActionTriggered(self, action):
        """Resolve preset/custom selection and emit the numeric interval in mm."""
        if action is self.replica_custom_action:
            value, accepted = QInputDialog.getDouble(
                self,
                "Custom replica interval",
                "Half-wavelength interval (mm):",
                self._replica_interval_mm,
                0.1,
                10000.0,
                1,
            )
            if not accepted:
                self.setReplicaInterval(self._replica_interval_mm)
                return
            interval_mm = float(value)
        else:
            interval_mm = float(action.data())
        self.setReplicaInterval(interval_mm)
        self.replicaIntervalChanged.emit(interval_mm)

    def _updateReplicaIntervalSelector(self, action, interval_mm):
        """Update Replica interval presentation without a checked tool button."""
        if action is self.replica_custom_action:
            label = f"{interval_mm:.1f} mm"
            description = f"Custom interval — {interval_mm:.1f} mm"
        else:
            label = f"{interval_mm:.1f} mm"
            description = action.text()
        tooltip = f"Replica interval: {description}"
        self.replica_interval_button.setIcon(QIcon())
        self.replica_interval_button.setText(label)
        self.replica_interval_button.setToolTip(tooltip)
        self.replica_interval_button.setStatusTip(tooltip)
        self.replica_interval_button.setWhatsThis(tooltip)
        self.replica_interval_button.setAccessibleName(tooltip)

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

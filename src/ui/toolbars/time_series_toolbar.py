"""Toolbar actions for the time-series plot panel."""

from qgis.PyQt.QtCore import QSize, pyqtSignal
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
from ..styles import (
    apply_command_toolbar_style,
    set_toolbar_control_role,
)
from ..widgets import SplitToolButton


class TimeSeriesToolbar(QToolBar):
    """Code-defined toolbar exposing semantic time-series action signals."""

    appearanceRequested = pyqtSignal()
    exportSettingsRequested = pyqtSignal()
    plotExportRequested = pyqtSignal()
    dataExportRequested = pyqtSignal()
    fitEnabledChanged = pyqtSignal(bool)
    fitModelChanged = pyqtSignal(str)
    seasonalEnabledChanged = pyqtSignal(bool)
    residualEnabledChanged = pyqtSignal(bool)
    xAxisModeChanged = pyqtSignal(str)
    manualXAxisEditRequested = pyqtSignal()
    yAxisModeChanged = pyqtSignal(str)
    manualYAxisEditRequested = pyqtSignal()
    replicaEnabledChanged = pyqtSignal(bool)
    replicaSettingsRequested = pyqtSignal()
    plotStyleRequested = pyqtSignal()

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
        self.addSeparator()

        self.x_axis_button = QToolButton(self)
        self.x_axis_button.setObjectName("tool_ts_x_axis")
        set_toolbar_control_role(self.x_axis_button, "selector")
        self.x_axis_button.setPopupMode(TOOL_BUTTON_INSTANT_POPUP)
        self.x_axis_menu = QMenu(self.x_axis_button)
        self.x_axis_menu.setObjectName("menu_ts_x_axis")
        self.x_axis_group = QActionGroup(self.x_axis_menu)
        self.x_axis_group.setExclusive(True)
        self.x_axis_actions = {}
        for mode, text, tooltip, icon_path, object_name in (
            (
                "from_data",
                "From data",
                "X-axis: From data\n\nUses the full available time range.",
                ":/icons/icons/x_axis_from_data.svg",
                "action_ts_x_from_data",
            ),
            (
                "manual",
                "Manual",
                "Manual time range\n\nNot configured",
                ":/icons/icons/x_axis_manual.svg",
                "action_ts_x_manual",
            ),
        ):
            action = QAction(QIcon(icon_path), text, self.x_axis_group)
            action.setObjectName(object_name)
            action.setCheckable(True)
            action.setData(mode)
            action.setToolTip(tooltip)
            self.x_axis_group.addAction(action)
            self.x_axis_menu.addAction(action)
            self.x_axis_actions[mode] = action
        self.x_axis_actions["from_data"].setChecked(True)
        self.x_axis_menu.addSeparator()
        self.edit_manual_x_axis_action = QAction("Edit range…", self.x_axis_menu)
        self.edit_manual_x_axis_action.setObjectName("action_ts_x_edit_manual")
        self.edit_manual_x_axis_action.setToolTip("Edit stored manual time range")
        self.x_axis_menu.addAction(self.edit_manual_x_axis_action)
        self.x_axis_button.setMenu(self.x_axis_menu)
        self.x_axis_button.setCheckable(False)
        self._updateXAxisSelector(self.x_axis_actions["from_data"])
        self.addWidget(self.x_axis_button)

        self.addSeparator()

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
            (
                "manual",
                "Manual",
                "Apply stored manual Y-axis ranges",
                ":/icons/icons/y_axis_manual.svg",
                "action_ts_y_manual",
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
        self.y_axis_menu.addSeparator()
        self.edit_manual_y_axis_action = QAction("Edit Manual ranges…", self.y_axis_menu)
        self.edit_manual_y_axis_action.setObjectName("action_ts_y_edit_manual")
        self.edit_manual_y_axis_action.setToolTip("Edit stored manual Y-axis ranges")
        self.y_axis_menu.addAction(self.edit_manual_y_axis_action)
        self.y_axis_button.setMenu(self.y_axis_menu)
        self.y_axis_button.setCheckable(False)
        self._updateYAxisSelector(self.y_axis_actions["from_data"])
        self.addWidget(self.y_axis_button)

        self.addSeparator()
        self.replica_button = SplitToolButton(
            icon=QIcon(":/icons/icons/replica.svg"),
            primary_checkable=True,
            parent=self,
            object_name="tool_ts_replica",
        )
        self.replica_button.setIconSize(self.iconSize())
        self.replica_button.setPrimaryAccessibleName("Replica")
        self.replica_button.setPrimaryAccessibleDescription(
            "Toggle Replica. Use the arrow for settings."
        )
        self.replica_button.setSecondaryToolTip("Replica settings")
        self.replica_button.setSecondaryAccessibleName("Replica settings")
        self.replica_button.setSecondaryAccessibleDescription(
            "Open Replica settings."
        )
        self.addWidget(self.replica_button)

        self.addSeparator()
        self.plot_style_action = self._createAction(
            ":/icons/icons/plot_settings.svg",
            "Plot style",
            "Edit the style of the current time series",
            "action_ts_plot_style",
        )
        self.addAction(self.plot_style_action)

        spacer = QWidget(self)
        spacer.setObjectName("timeSeriesToolbarSpacer")
        spacer.setSizePolicy(
            SIZE_POLICY_EXPANDING,
            SIZE_POLICY_PREFERRED,
        )
        self.addWidget(spacer)

        self.appearance_action = self._createAction(
            ":/icons/icons/setting.svg",
            "Appearance",
            "Appearance",
            "action_ts_appearance",
        )
        self.export_settings_action = self._createAction(
            ":/icons/icons/screenshot_settings.svg",
            "Export settings",
            "Export settings",
            "action_ts_export_settings",
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

        self.addAction(self.appearance_action)
        self.addSeparator()
        self.addAction(self.export_settings_action)
        self.addAction(self.plot_export_action)
        self.addAction(self.data_export_action)

        for action in (
            self.fit_enabled_action,
            self.seasonal_action,
            self.residual_action,
        ):
            self._setActionControlRole(action, "toggle")
        for action in (
            self.appearance_action,
            self.export_settings_action,
            self.plot_export_action,
            self.data_export_action,
            self.plot_style_action,
        ):
            self._setActionControlRole(action, "command")

        self.plot_style_action.triggered.connect(self.plotStyleRequested.emit)
        self.appearance_action.triggered.connect(self.appearanceRequested.emit)
        self.export_settings_action.triggered.connect(self.exportSettingsRequested.emit)
        self.plot_export_action.triggered.connect(self.plotExportRequested.emit)
        self.data_export_action.triggered.connect(self.dataExportRequested.emit)
        self.fit_enabled_action.toggled.connect(self.fitEnabledChanged.emit)
        self.fit_model_group.triggered.connect(self._fitModelActionTriggered)
        self.seasonal_action.toggled.connect(self.seasonalEnabledChanged.emit)
        self.residual_action.toggled.connect(self.residualEnabledChanged.emit)
        self.x_axis_group.triggered.connect(self._xAxisActionTriggered)
        self.edit_manual_x_axis_action.triggered.connect(self.manualXAxisEditRequested.emit)
        self.y_axis_group.triggered.connect(self._yAxisActionTriggered)
        self.edit_manual_y_axis_action.triggered.connect(self.manualYAxisEditRequested.emit)
        self.replica_button.primaryToggled.connect(self.replicaEnabledChanged.emit)
        self.replica_button.secondaryTriggered.connect(self.replicaSettingsRequested.emit)

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

    def setSelectedXAxisMode(self, mode, start=None, end=None, custom_view=False):
        """Update the selected X-axis mode without emitting a user-change signal."""
        self.refreshXAxisPresentation(mode, start, end, custom_view=custom_view)

    def refreshXAxisPresentation(self, mode, start=None, end=None, custom_view=False):
        """Refresh all temporary X-axis toolbar compatibility views.

        TODO(phase-appearance-toolbar): remove this compatibility presentation
        helper when toolbar controls bind directly to the runtime settings model.
        """
        mode = mode if mode in self.x_axis_actions else "from_data"
        action = self.x_axis_actions[mode]
        manual_action = self.x_axis_actions["manual"]
        manual_action.setText("Manual")
        if start is None or end is None:
            manual_tooltip = "Manual time range\n\nNot configured"
        else:
            manual_tooltip = f"Manual time range\n\n{start:%Y-%m-%d}\n→\n{end:%Y-%m-%d}"
        manual_action.setToolTip(manual_tooltip)

        previous = self.x_axis_group.blockSignals(True)
        action.setChecked(True)
        self.x_axis_group.blockSignals(previous)
        self._updateXAxisSelector(action, custom_view=custom_view)

    def setManualXAxisSummary(self, start, end):
        """Refresh Manual metadata while preserving the selected policy."""
        selected = self.x_axis_group.checkedAction()
        mode = selected.data() if selected is not None else "from_data"
        self.refreshXAxisPresentation(mode, start, end)

    def _xAxisActionTriggered(self, action):
        """Emit the requested policy; the controller owns presentation refresh."""
        self.xAxisModeChanged.emit(action.data())

    def _updateXAxisSelector(self, action, *, custom_view=False):
        """Render X-axis presentation from the base policy and transient viewport state."""
        if custom_view:
            tooltip = f"Custom X view\nBase policy: {action.text()}"
            self.x_axis_button.setIcon(QIcon(":/icons/icons/x_axis_custom.svg"))
        else:
            tooltip = action.toolTip()
            self.x_axis_button.setIcon(action.icon())
        self.x_axis_button.setText(action.text())
        self.x_axis_button.setToolTip(tooltip)
        self.x_axis_button.setStatusTip(tooltip)
        self.x_axis_button.setWhatsThis(tooltip)
        self.x_axis_button.setAccessibleName(f"Selected X-axis mode: {action.text()}")

    def setSelectedYAxisMode(self, mode, lower=None, upper=None, residual_lower=None, residual_upper=None, residual_active=True, series_custom_view=False, residual_custom_view=False):
        """Update the selected Y-axis mode without emitting a user-change signal."""
        self.refreshYAxisPresentation(
            mode, lower, upper, residual_lower, residual_upper, residual_active,
            series_custom_view, residual_custom_view,
        )

    def refreshYAxisPresentation(self, mode, lower=None, upper=None, residual_lower=None, residual_upper=None, residual_active=True, series_custom_view=False, residual_custom_view=False):
        """Refresh checked policy, icon, label, and tooltip from runtime Y state."""
        action = self.y_axis_actions[mode]
        if mode == "manual":
            self.setManualYAxisSummary(lower, upper, residual_lower, residual_upper, residual_active)
        previous = self.y_axis_group.blockSignals(True)
        action.setChecked(True)
        self.y_axis_group.blockSignals(previous)
        self._updateYAxisSelector(
            action,
            series_custom_view=series_custom_view,
            residual_custom_view=residual_custom_view,
        )

    def setManualYAxisSummary(self, lower, upper, residual_lower=None, residual_upper=None, residual_active=True):
        """Update Manual action text and metadata with its configured bounds."""
        def display(value):
            if value is None:
                return "Auto"
            return f"{value:g}"

        action = self.y_axis_actions["manual"]
        action.setText("Manual")
        residual_summary = (
            f"{display(residual_lower)} to {display(residual_upper)}"
            if residual_active
            else "Inactive"
        )
        action.setToolTip(
            f"Time series: {display(lower)} to {display(upper)}\n"
            f"Residuals: {residual_summary}"
        )
        if action.isChecked():
            self._updateYAxisSelector(action)

    def _yAxisActionTriggered(self, action):
        """Emit the requested policy; the controller owns presentation refresh."""
        self.yAxisModeChanged.emit(action.data())

    def _updateYAxisSelector(self, action, *, series_custom_view=False, residual_custom_view=False):
        """Render Y-axis presentation from policy plus independent viewport states."""
        if series_custom_view:
            self.y_axis_button.setIcon(QIcon(":/icons/icons/y_axis_custom.svg"))
            tooltip = f"Time series: Custom view\nBase policy: {action.text()}"
        else:
            self.y_axis_button.setIcon(action.icon())
            tooltip = action.toolTip()
        if residual_custom_view:
            tooltip += "\nResiduals: Custom view"
        self.y_axis_button.setText(action.text())
        self.y_axis_button.setToolTip(tooltip)
        self.y_axis_button.setStatusTip(tooltip)
        self.y_axis_button.setWhatsThis(tooltip)
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

    def setReplicaPresentation(self, enabled, interval_mm, pair_count):
        """Refresh the Replica split button without changing runtime state."""
        enabled = bool(enabled)
        toggle_tooltip = "Disable Replica" if enabled else "Enable Replica"
        description = (
            f"Replica enabled; interval {float(interval_mm):.1f} mm; "
            f"{int(pair_count)} pair(s)."
            if enabled else "Replica disabled."
        )

        self.replica_button.setChecked(enabled)
        self.replica_button.setPrimaryToolTip(toggle_tooltip)
        self.replica_button.setPrimaryStatusTip(description)
        self.replica_button.setPrimaryAccessibleDescription(
            "Toggle Replica. Use the arrow for settings. " + description
        )
        self.replica_button.setStatusTip(description)

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

import os

from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtWidgets import QFileDialog, QMenu, QComboBox
from qgis.PyQt.QtCore import QObject, QPoint, QRect, QSettings, QStandardPaths, QTimer, QVariant, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QTransform

from . import map_click_handler as cph
from . import setup_frames
from .map_setting import InsarMap
from .layer_utils import vector_layer as vector_layer_utils
from .about import about as insar_explorer_about
from ..external.setting_manager_ui.setting_ui import SettingsTableDialog
from ..external.setting_manager_ui.json_settings import JsonSettings
from .drawing_tools.polygon_drawing_tool import PolygonDrawingTool
from .ui_windows.color_picker import ColorPicker
from .ui.popups.time_series_style_popup import TimeSeriesStylePopup
from .qt_compat import (
    RASTER_LAYER,
    VECTOR_LAYER,
    available_screen_geometry,
    screen_aware_popup_position,
)
from .time_series.fit_state import TimeSeriesFitState
from .time_series.style_controller import TimeSeriesStyleController
from .time_series.style_persistence import persist_default_time_series_style


class GuiController(QObject):
    msg_signal = pyqtSignal(str, str, int)

    def __init__(self, plugin):
        super().__init__()
        self.iface = plugin.iface
        self.ui = plugin.dockwidget
        self.choose_point_click_handler = cph.ClickHandler(plugin, msg_signal=self.msg_signal)
        self.click_tool = None  # plugin.click_tool
        self.drawing_tool = None  # for polygon drawing
        self.drawing_tool_reference = None  # for reference polygon drawing
        self.selection_type = "point"  # "point" or "polygon" or "reference polygon"
        self.time_series_fit_state = TimeSeriesFitState()
        self.initializeSelection()
        setup_frames.setupTsFrame(self.ui)
        self.insar_map = InsarMap(self.iface)
        self.settings = QSettings()
        self.time_series_y_axis_mode = self._loadTimeSeriesYAxisMode()
        self.time_series_replica_enabled = self.settings.value(
            "insar_explorer/replica_enabled", False, type=bool
        )
        self.time_series_replica_interval_mm = self._loadReplicaInterval()
        self.time_series_replica_pair_count = self._loadReplicaPairCount()
        self.time_series_style_popup = TimeSeriesStylePopup(self.ui)
        self.time_series_style_controller = TimeSeriesStyleController()
        self.last_save_path = self._initialExportDirectory()
        self.last_save_ts_name = "ts_plot.png"
        self.last_export_ts_name = "ts_data.csv"
        self.last_plot_export_format = self.settings.value(
            'insar_explorer/plot_export_format', 'png', type=str
        )
        self.last_ts_export_format = self.settings.value(
            'insar_explorer/ts_export_format', 'csv', type=str
        )
        self.initializeUiParams()
        self.connectUiSignals()
        # make point selection active by default
        self.ui.pb_choose_point.setChecked(True)
        self.activatePointSelection(True)

        # add data range menu
        self.setDataRangeMenu()

        self.iface.currentLayerChanged.connect(self.onLayerChanged)
        self.onLayerChanged()

        self.setVectorFields()

    def initializeUiParams(self):
        """Initialize code-created controls; migrated style controls live in the popup."""
        return

    def initializeSelection(self):
        if self.selection_type == "point":
            self.initializeClickTool()
        elif self.selection_type == "polygon":
            self.initializePolygonDrawingTool()
        elif self.selection_type == "reference polygon":
            self.initializePolygonDrawingTool(reference=True)

    def onLayerChanged(self, layer=None):
        """Reset the click handler and the map when the active layer changes."""
        if layer is None:
            layer = self.iface.activeLayer()
        if layer:
            self.choose_point_click_handler.reset()
            self._restoreTimeSeriesFitState()
            self._restoreTimeSeriesYAxisMode()
            self._restoreTimeSeriesReplicaState()
            self.insar_map.reset()
            self.setVectorFields()

            layer_type = layer.type()
            is_local_raster = (hasattr(layer, "dataProvider") and getattr(layer.dataProvider(), "name", lambda: "")()
                               in ["gdal"])  # "ogr"

            if layer_type == VECTOR_LAYER:
                self.ui.pb_choose_polygon.setEnabled(True)
                self.ui.pb_set_reference_polygon.setEnabled(True)
            elif layer_type == RASTER_LAYER:
                self.ui.tab_config_panel.setEnabled(False)
                self.ui.pb_choose_polygon.setEnabled(False)
                self.ui.pb_set_reference_polygon.setEnabled(False)

            if layer_type == RASTER_LAYER and not is_local_raster:
                self.ui.tab_config_panel.setEnabled(False)
                self.ui.pb_choose_point.setChecked(False)
                message = "Unsupported layer selected. Please choose a layer compatible with InSAR Explorer."
            else:
                self.ui.tab_config_panel.setEnabled(True)
                self.ui.pb_choose_point.setChecked(True)
                message = ""
            self.msg_signal.emit(message, "i", 0)

    def setVectorFields(self):
        layer = self.iface.activeLayer()
        if not layer:
            return
        status, message = vector_layer_utils.checkVectorLayer(layer)
        self.ui.cb_select_field.clear()
        if status is False:
            self.ui.cb_select_field.setEnabled(False)
            self.ui.sb_symbol_size.setEnabled(False)
            return
        else:
            self.ui.cb_select_field.setEnabled(True)
            self.ui.sb_symbol_size.setEnabled(True)

        field_list, field_types = vector_layer_utils.getVectorFields(layer)
        velocity_field, message = vector_layer_utils.getVectorVelocityFieldName(layer)

        for field, field_type in zip(field_list, field_types):
            self.ui.cb_select_field.addItem(field)
            if field_type not in [QVariant.Double, QVariant.Int, QVariant.LongLong]:
                index = self.ui.cb_select_field.count() - 1
                self.ui.cb_select_field.model().item(index).setEnabled(False)

        if velocity_field:
            self.ui.cb_select_field.setCurrentText(velocity_field)

        self.insar_map.reset()
        self.insar_map.selected_field_name = self.ui.cb_select_field.currentText()

    def selectVectorFieldChanged(self):
        self.insar_map.selected_field_name = self.ui.cb_select_field.currentText()
        self.choose_point_click_handler.selected_field_name = self.insar_map.selected_field_name
        self.insar_map.reset()
        self.applyLiveSymbology()

    def initializeClickTool(self):
        if not self.click_tool:
            self.click_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
            self.click_tool.canvasClicked.connect(lambda point: self.onMapClicked(point=point))

    def onMapClicked(self, point):
        self.msg_signal.emit("", "i", 0)
        self.choose_point_click_handler.choosePointClicked(point=point, layer=None,
                                                           ref=self.ui.pb_set_reference.isChecked(),
                                                           start_callback=self.removePolygonDrawingTool(
                                                               self.ui.pb_set_reference.isChecked()))

        if self.ui.pb_set_reference.isChecked():
            self.syncOffsetWithReference()

    def removeClickTool(self):
        self.iface.mapCanvas().unsetMapTool(self.click_tool)
        self.click_tool = None

    def initializePolygonDrawingTool(self, reference=False):
        if not reference:
            if not self.drawing_tool:
                self.drawing_tool = (
                    PolygonDrawingTool(self.iface.mapCanvas(), callback=self.polygonDrawnCallback,
                                       start_callback=self.choose_point_click_handler.clearFeatureHighlight))
            # FIXME: when push button is reactivated, current polygon is removed
            self.iface.mapCanvas().setMapTool(self.drawing_tool)
        else:
            if not self.drawing_tool_reference:
                self.drawing_tool_reference = (
                    PolygonDrawingTool(self.iface.mapCanvas(), callback=self.polygonDrawnCallback,
                                       start_callback=self.choose_point_click_handler.clearReferenceFeatureHighlight))
                self.drawing_tool_reference.polygon_marker.setStyle(color=(255, 100, 100, 80))
            self.iface.mapCanvas().setMapTool(self.drawing_tool_reference)

    def deactivatePolygonDrawingTool(self, reference=False):
        if not reference and self.drawing_tool:
            self.iface.mapCanvas().unsetMapTool(self.drawing_tool)
        elif reference and self.drawing_tool_reference:
            self.iface.mapCanvas().unsetMapTool(self.drawing_tool_reference)

    def removePolygonDrawingTool(self, reference=False):
        self.deactivatePolygonDrawingTool(reference=reference)
        if not reference and self.drawing_tool:
            self.drawing_tool.clear()
            self.drawing_tool = None
        elif reference and self.drawing_tool_reference:
            self.drawing_tool_reference.clear()
            self.drawing_tool_reference = None

    def polygonDrawnCallback(self, polygon):
        self.choose_point_click_handler.choosePolygonDrawn(polygon=polygon,
                                                           ref=self.ui.pb_set_reference_polygon.isChecked())
        self.syncOffsetWithReference()

    def syncOffsetWithReference(self):
        """Sync offset value with reference point or polygon."""
        if self.ui.cb_symbol_value_offset_sync_with_ref.isChecked():
            value = self.choose_point_click_handler.map_reference_clicked_value
            self.insar_map.offset_value = value
            self.ui.sb_symbol_value_offset.setValue(value)
            self.applySymbology()

    def connectUiSignals(self):
        self.ui.visibilityChanged.connect(self.handleUiClose)
        # self.ui.pb_add_layers.clicked.connect(self.addSelectedLayers)
        # self.ui.pb_remove_layers.clicked.connect(self.removeSelectedLayers)
        self.connectTimeseriesSignals()
        self.connectMapSignals()

        self.connectAboutSignals()
        self.msg_signal.connect(self.setMessageBar)

    def setMessageBar(self, message, v, t):

        width = self.ui.lb_msg_bar.width()
        font_metrics = self.ui.lb_msg_bar.fontMetrics()
        avg_char_width = max(1, font_metrics.horizontalAdvance(str(message)) // max(1, len(str(message))))
        buffer = 50
        num_chars = max(50, (width - buffer) // avg_char_width)

        info = ""
        tip = "💡 "
        warning, error, done = [f'<span style="font-size:10px">{s}</span>&nbsp;' for s in ["🟡️", "🟠", "🟢"]]

        if message == "":
            v = ''

        if v == 'w':
            message = warning + str(message)
        elif v == 'e':
            message = error + str(message)
        elif v == 'i':
            message = info + str(message)
        elif v == 't':
            message = tip + str(message)
        elif v == 'done':
            message = done + str(message)
        else:
            message = str(message)

        self.ui.lb_msg_bar.setText(message[:num_chars])

        if t > 0:
            # reset timer
            if not hasattr(self, '_msg_timer'):
                self._msg_timer = QTimer(self.ui)
                self._msg_timer.setSingleShot(True)
                self._msg_timer.timeout.connect(lambda: self.setMessageBar("", "", 0))
            self._msg_timer.stop()
            self._msg_timer.start(t)

    def connectAboutSignals(self):
        self.ui.label_about.setOpenExternalLinks(False)
        self.ui.label_about.linkActivated.connect(self.aboutLabelClicked)

    def aboutLabelClicked(self):
        from .ui_windows.message_box import MessageBox
        text = insar_explorer_about
        MessageBox(text)

    def connectTimeseriesSignals(self):
        self.ui.pb_choose_point.clicked.connect(self.activatePointSelection)
        self.ui.pb_set_reference.clicked.connect(self.activateReferencePointSelection)
        self.ui.pb_reset_reference.clicked.connect(self.resetReferencePoint)
        self.ui.pb_choose_polygon.clicked.connect(self.activatePolygonSelection)
        self.ui.pb_set_reference_polygon.clicked.connect(self.activateReferencePolygonSelection)
        self.ui.cb_symbol_value_offset_sync_with_ref.clicked.connect(self.syncOffsetWithReferenceClicked)
        # TS fit handler
        self.ui.time_series_toolbar.fitEnabledChanged.connect(self.setTimeSeriesFitEnabled)
        self.ui.time_series_toolbar.fitModelChanged.connect(self.setTimeSeriesFitModel)
        self.ui.time_series_toolbar.seasonalEnabledChanged.connect(self.setTimeSeriesSeasonalEnabled)
        self.ui.time_series_toolbar.residualEnabledChanged.connect(self.setTimeSeriesResidualEnabled)
        self.ui.time_series_toolbar.yAxisModeChanged.connect(self.setTimeSeriesYAxisMode)
        self.ui.time_series_toolbar.replicaEnabledChanged.connect(
            self.setTimeSeriesReplicaEnabled
        )
        self.ui.time_series_toolbar.replicaIntervalChanged.connect(
            self.setTimeSeriesReplicaInterval
        )
        self.ui.time_series_toolbar.replicaPairCountChanged.connect(
            self.setTimeSeriesReplicaPairCount
        )
        self.ui.time_series_toolbar.plotStyleRequested.connect(self.showTimeSeriesStylePopup)
        popup = self.time_series_style_popup
        popup.markerTypeChanged.connect(lambda value: self._applySelectedSeriesStyle("marker_type", value))
        popup.markerColorChanged.connect(lambda value: self._applySelectedSeriesStyle("marker_color", value))
        popup.markerSizeChanged.connect(lambda value: self._applySelectedSeriesStyle("marker_size", value))
        popup.lineTypeChanged.connect(lambda value: self._applySelectedSeriesStyle("line_type", value))
        popup.lineColorChanged.connect(lambda value: self._applySelectedSeriesStyle("line_color", value))
        popup.lineWidthChanged.connect(lambda value: self._applySelectedSeriesStyle("line_width", value))
        popup.randomizeColorRequested.connect(self.randomizeSelectedTimeSeriesColor)
        popup.setCurrentStyleAsDefaultRequested.connect(self.setCurrentSeriesStyleAsDefault)
        self._restoreTimeSeriesFitState()
        # Plot setting
        self._restoreTimeSeriesYAxisMode()
        self._restoreTimeSeriesReplicaState()
        self.ui.cb_hold_on_plot.toggled.connect(self.holdOnPlot)
        self.ui.cb_remove_last_plot.clicked.connect(self.removeLastPlotClicked)
        # TS save
        self.ui.time_series_toolbar.plotExportRequested.connect(self.saveTsPlot)
        self.ui.time_series_toolbar.dataExportRequested.connect(self.exportTs)

        # Setting popup
        self.ui.time_series_toolbar.settingsRequested.connect(self.settingsWidgetPopup)

    def connectMapSignals(self):
        self.ui.cb_select_field.currentTextChanged.connect(self.selectVectorFieldChanged)
        self.ui.pb_symbology.clicked.connect(self.applySymbologyClicked)
        self.ui.sb_symbol_lower_range.valueChanged.connect(self.setSymbologyLowerRange)
        self.ui.sb_symbol_upper_range.valueChanged.connect(self.setSymbologyUpperRange)
        self.ui.cb_symbol_range_sync.clicked.connect(self.symbologyRangeSyncClicked)
        self.ui.sb_symbol_value_offset.valueChanged.connect(self.setSymbologyOffset)
        self.ui.sb_symbol_classes.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_size.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_opacity.valueChanged.connect(self.applyLiveSymbology)
        self.ui.pb_symbology_live.toggled.connect(self.activateLiveSymbology)
        self.ui.cmb_colormap.currentIndexChanged.connect(self.applyLiveSymbology)
        self.ui.pb_colormap_reverse.toggled.connect(self.colormapReverseClicked)

    def setDataRangeMenu(self):
        """creat a menu for setting data range"""
        menu = QMenu(self.ui)
        menu.addAction("Range from data", self.setSymbologyRangeFromData)
        menu.addAction("1xStd", self.setSymbologyRangeFromData)
        menu.addAction("2xStd", self.setSymbologyRangeFromData)
        menu.addAction("3xStd", self.setSymbologyRangeFromData)
        self.ui.pb_range_from_data.setMenu(menu)

    def settingsWidgetPopup(self):
        self.msg_signal.emit("", "", 0)
        json_file = "config/config.json"
        block_key = "timeseries settings"
        script_path = os.path.abspath(__file__)
        json_file_path = os.path.join(os.path.dirname(script_path), json_file)
        dialog = SettingsTableDialog(json_file_path, block_key=block_key)
        dialog.accepted.connect(self.onSettingDialogChanged)
        dialog.applyClicked.connect(self.onSettingDialogChanged)
        dialog.exec()
        self.initializeUiParams()

    def onSettingDialogChanged(self):
        """Reload externally edited Replica settings before one plot redraw."""
        self._reloadReplicaPairCountFromConfig()
        self.choose_point_click_handler.plot_ts.plotTs(update=True)

    def setSymbologyUpperRange(self):
        self.ui.sb_symbol_lower_range.blockSignals(True)
        if self.ui.cb_symbol_range_sync.isChecked():
            value = self.ui.sb_symbol_upper_range.value()
            self.ui.sb_symbol_lower_range.setValue(-value)
        self.ui.sb_symbol_lower_range.blockSignals(False)
        self.applyLiveSymbology()

    def setSymbologyLowerRange(self):
        self.ui.sb_symbol_upper_range.blockSignals(True)
        if self.ui.cb_symbol_range_sync.isChecked():
            value = self.ui.sb_symbol_lower_range.value()
            self.ui.sb_symbol_upper_range.setValue(-value)
        self.ui.sb_symbol_upper_range.blockSignals(False)
        self.applyLiveSymbology()

    def symbologyRangeSyncClicked(self, status):
        if status:
            self.setSymbologyLowerRange()
            self.msg_signal.emit("Symbology range synced: changing one value updates the other.", 't', 0)
        else:
            self.msg_signal.emit("Symbology ranges unsynced.", 'i', 0)

    def setSymbologyOffset(self):
        self.insar_map.offset_value = self.ui.sb_symbol_value_offset.value()
        self.applyLiveSymbology()

    def setSymbologyRangeFromData(self):
        button = self.sender()
        if button.text() == "Range from data":
            message = self.insar_map.setSymbologyRangeFromData()
            message = "Symbology range set from data."
        elif button.text() == "1xStd":
            message = self.insar_map.setSymbologyRangeFromData(n_std=1)
            message = "Symbology range set to mean±1σ."
        elif button.text() == "2xStd":
            message = self.insar_map.setSymbologyRangeFromData(n_std=2)
            message = "Symbology range set to mean±2σ."
        elif button.text() == "3xStd":
            message = self.insar_map.setSymbologyRangeFromData(n_std=3)
            message = "Symbology range set to mean±3σ."

        self.msg_signal.emit(message, 'i', 0)
        min_value = self.insar_map.min_value
        max_value = self.insar_map.max_value
        if self.ui.cb_symbol_range_sync.isChecked():
            max_value = max(abs(min_value), abs(max_value))
            min_value = -max_value
        self.ui.sb_symbol_lower_range.setValue(min_value)
        self.ui.sb_symbol_upper_range.setValue(max_value)

    def applyLiveSymbology(self):
        if self.ui.pb_symbology_live.isChecked():
            self.applySymbology()

    def activateLiveSymbology(self, status):
        if status:
            self.applyLiveSymbology()
            self.msg_signal.emit("Live symbology enabled: changes will apply immediately.", 'done', 0)
        else:
            self.msg_signal.emit("Live symbology disabled.", 'i', 0)

    def applySymbologyNow(self):
        QTimer.singleShot(0, self.applySymbology)

    def applySymbology(self):
        self.insar_map.selected_field_name = self.ui.cb_select_field.currentText()
        self.insar_map.min_value = float(self.ui.sb_symbol_lower_range.value())
        self.insar_map.max_value = float(self.ui.sb_symbol_upper_range.value())
        self.insar_map.num_classes = int(self.ui.sb_symbol_classes.value())
        self.insar_map.alpha = float(self.ui.sb_symbol_opacity.value()) / 100
        self.insar_map.symbol_size = float(self.ui.sb_symbol_size.value())
        self.insar_map.color_ramp_name = self.ui.cmb_colormap.currentText()
        message = self.insar_map.setSymbology()
        if message != "":
            self.msg_signal.emit(message, "i", 0)
        else:
            self.msg_signal.emit("", "", 0)

    def applySymbologyClicked(self, status):
        self.applySymbology()
        self.msg_signal.emit("Symbology applied.", "done", 5000)

    def colormapReverseClicked(self, status):
        if status:
            self.msg_signal.emit("Colormap reversed.", "i", 0)
        else:
            self.msg_signal.emit("Colormap normal.", "i", 0)
        self.flipComboBoxIcons(self.ui.cmb_colormap)
        self.insar_map.color_ramp_reverse_flag = status
        self.applyLiveSymbology()

    def flipComboBoxIcons(self, combo_box: QComboBox):
        for index in range(combo_box.count()):
            icon = combo_box.itemIcon(index)
            if not icon.isNull():
                pixmap = icon.pixmap(icon.availableSizes()[0])
                transform = QTransform().scale(-1, 1)  # fip horizontally
                flipped_pixmap = pixmap.transformed(transform)
                combo_box.setItemIcon(index, QIcon(flipped_pixmap))

    def _restoreTimeSeriesFitState(self):
        """Restore session fit state after UI, plotter, or layer lifecycle changes."""
        state = self.time_series_fit_state
        state.setSelectedModel(state.selected_fit_model)
        self._applyTimeSeriesFitState(refresh=False)

    def resetTimeSeriesFitState(self):
        """Reset fit activity while retaining a valid selected model for this session."""
        self.time_series_fit_state.setFitEnabled(False)
        self.time_series_fit_state.residual_enabled = False
        self._applyTimeSeriesFitState(refresh=False)

    def _syncTimeSeriesFitControls(self):
        """Synchronize the code-created toolbar from shared fit state."""
        state = self.time_series_fit_state
        toolbar = self.ui.time_series_toolbar
        toolbar.setFitEnabled(state.fit_enabled)
        toolbar.setSelectedFitModel(state.selected_fit_model)
        toolbar.setSeasonalEnabled(state.seasonal_enabled)
        toolbar.setResidualEnabled(state.residual_enabled)

    def _applyTimeSeriesFitState(self, refresh=True):
        """Apply fit state to the plotter and both temporary UI surfaces."""
        state = self.time_series_fit_state
        plotter = self.choose_point_click_handler.plot_ts
        plotter.fit_models = [state.selected_fit_model] if state.fit_enabled else []
        plotter.fit_seasonal_flag = state.seasonal_enabled
        plotter.plot_residuals_flag = state.residual_enabled and state.fit_enabled
        self._syncTimeSeriesFitControls()
        if refresh:
            plotter.plotTs(update=True)

    def setTimeSeriesFitEnabled(self, enabled):
        """Enable or disable the currently selected model in one operation."""
        self.time_series_fit_state.setFitEnabled(enabled)
        self._applyTimeSeriesFitState()
        if enabled:
            self.msg_signal.emit(
                f"Fit model selected: {self.time_series_fit_state.selected_fit_model}", "i", 0
            )
        else:
            self.msg_signal.emit("No fit model selected.", "i", 0)

    def setTimeSeriesFitModel(self, model):
        """Select a model and refresh only when fitting is active."""
        self.time_series_fit_state.setSelectedModel(model)
        self._applyTimeSeriesFitState(refresh=self.time_series_fit_state.fit_enabled)

    def setTimeSeriesSeasonalEnabled(self, enabled):
        """Set seasonal fitting and activate fitting when seasonal is enabled."""
        self.time_series_fit_state.setSeasonalEnabled(enabled)
        self._applyTimeSeriesFitState()
        self.msg_signal.emit(
            "Seasonal fit enabled using the selected model."
            if enabled else "Seasonal fit disabled.", "i", 0
        )

    def setTimeSeriesResidualEnabled(self, enabled):
        """Set residual visibility and activate fitting when residuals are enabled."""
        self.time_series_fit_state.setResidualEnabled(enabled)
        self._applyTimeSeriesFitState()
        self.msg_signal.emit(
            "Residual plot enabled using the selected fit model."
            if enabled else "Residual plot disabled.", "i", 0
        )

    def selectedTimeSeriesSnapshots(self):
        """Return all explicit style-edit targets for current and future selection UIs."""
        return self.choose_point_click_handler.plot_ts.selectedTimeSeriesSnapshots()

    def selectedSeriesStyles(self):
        """Return styles for all currently selected time-series snapshots."""
        return self.time_series_style_controller.selectedSeriesStyles(
            self.selectedTimeSeriesSnapshots()
        )

    def _selectedTimeSeriesSnapshots(self):
        """Return explicit current style-edit targets from the plotter selection API."""
        return self.selectedTimeSeriesSnapshots()

    def _applySelectedSeriesStyle(self, property_name, value):
        """Apply one style property to selected series and redraw exactly once."""
        snapshots = self._selectedTimeSeriesSnapshots()
        if not snapshots:
            return
        changed = self.time_series_style_controller.applyProperty(snapshots, property_name, value)
        self.choose_point_click_handler.plot_ts.rerenderTimeSeriesSnapshots(changed)

    def randomizeSelectedTimeSeriesColor(self):
        """Randomize only selected series colors while preserving future defaults."""
        snapshots = self._selectedTimeSeriesSnapshots()
        if not snapshots:
            return
        changed = self.time_series_style_controller.randomizeColor(snapshots)
        self.choose_point_click_handler.plot_ts.rerenderTimeSeriesSnapshots(changed)
        self.time_series_style_popup.setStyle(changed[0].style)

    def setCurrentSeriesStyleAsDefault(self):
        """Persist the selected series style as the default for newly-created series."""
        snapshots = self._selectedTimeSeriesSnapshots()
        if not snapshots:
            return
        style = snapshots[0].style
        persist_default_time_series_style(
            self.choose_point_click_handler.plot_ts.config_file,
            style,
        )
        self.choose_point_click_handler.plot_ts.default_style.replaceFromSeries(style)
        self.msg_signal.emit("Current plot style set as default for new time series.", "done", 3000)

    def showTimeSeriesStylePopup(self):
        """Open the style popup anchored below the Plot style toolbar action."""
        plotter = self.choose_point_click_handler.plot_ts
        snapshots = plotter.selectedTimeSeriesSnapshots()
        self.time_series_style_popup.setSelectionState(bool(snapshots), len(snapshots))
        if snapshots:
            styles = self.time_series_style_controller.selectedSeriesStyles(snapshots)
            self.time_series_style_popup.setStyle(styles[0])
            self.time_series_style_popup.setMixedProperties(
                self.time_series_style_controller.mixedProperties(snapshots)
            )
        toolbar = self.ui.time_series_toolbar
        action_widget = toolbar.widgetForAction(toolbar.plot_style_action)
        anchor = action_widget or toolbar
        self.time_series_style_popup.adjustSize()
        anchor_top_left = anchor.mapToGlobal(QPoint(0, 0))
        anchor_rect = QRect(anchor_top_left, anchor.size())
        available_geometry = available_screen_geometry(anchor_rect.center(), anchor)
        point = screen_aware_popup_position(
            anchor_rect,
            self.time_series_style_popup.sizeHint(),
            available_geometry,
        )
        self.time_series_style_popup.move(point)
        self.time_series_style_popup.show()
        self.time_series_style_popup.raise_()

    def holdOnPlot(self, status):
        self.choose_point_click_handler.plot_ts.hold_on_flag = status
        if status:
            self.msg_signal.emit("Hold on plot enabled: new plots will be added to the existing plot.", "i", 0)
        else:
            self.msg_signal.emit("Hold on plot disabled.", "i", 0)

    def removeLastPlotClicked(self):
        # TODO: remove the last plot and show the previous plot polygon/point highlight
        self.choose_point_click_handler.removeLastPlot()
        # TODO: move polygon drawing methods to PolygonDrawingTool class
        self.removePolygonDrawingTool(reference=False)
        self.removePolygonDrawingTool(reference=True)

    def updateConfigFile(self, key_list, value_type, new_value=None):
        block_key = "timeseries settings"
        parms = JsonSettings(self.choose_point_click_handler.plot_ts.config_file)
        settings_block = parms.load(block_key=block_key)

        if value_type == "string":
            new_value = str(new_value)

        if value_type == "float":
            new_value = float(new_value)

        if value_type == "color":
            initial_value = parms.get(key_list) or "#000000"
            color_picker = ColorPicker(parent=self.ui, initial_color=initial_value, use_native_flag=False)
            new_value = color_picker.pickColor()

        settings_ref = settings_block
        for key in key_list:
            settings_ref = settings_ref[key]
        settings_ref["value"] = new_value

        parms.save(block_key, settings_block)
        return new_value

    def _loadTimeSeriesYAxisMode(self):
        """Load and validate the persisted Time Series Y-axis mode."""
        mode = self.settings.value(
            "insar_explorer/time_series_y_axis_mode", "from_data", type=str
        )
        return mode if mode in {"from_data", "symmetric", "adaptive"} else "from_data"

    def _restoreTimeSeriesYAxisMode(self):
        """Restore the selected Y-axis mode after UI or plotter lifecycle changes."""
        self._applyTimeSeriesYAxisMode(self.time_series_y_axis_mode, refresh=False)

    def _syncTimeSeriesYAxisControls(self, mode):
        """Synchronize the code-created toolbar from shared Y-axis state."""
        self.ui.time_series_toolbar.setSelectedYAxisMode(mode)

    def _applyTimeSeriesYAxisMode(self, mode, refresh=True):
        """Apply one validated Y-axis mode and optionally redraw the active plot."""
        if mode not in {"from_data", "symmetric", "adaptive"}:
            mode = "from_data"
        self.time_series_y_axis_mode = mode
        self.choose_point_click_handler.plot_ts.plot_y_axis = mode
        self._syncTimeSeriesYAxisControls(mode)
        self.settings.setValue("insar_explorer/time_series_y_axis_mode", mode)
        if refresh:
            self.choose_point_click_handler.plot_ts.plotTs(update=True)

    def setTimeSeriesYAxisMode(self, mode):
        """Handle a toolbar Y-axis selection with one state update and redraw."""
        self._applyTimeSeriesYAxisMode(mode)
        messages = {
            "from_data": "Y-axis range set from data.",
            "symmetric": "Y-axis range set symmetric.",
            "adaptive": (
                "Y-axis range set adaptively: less range change when plotting new time series."
            ),
        }
        self.msg_signal.emit(messages[self.time_series_y_axis_mode], "i", 0)

    def _loadReplicaInterval(self):
        """Load and validate the persisted replica half-wavelength interval."""
        value = self.settings.value(
            "insar_explorer/replica_interval_mm", 27.8, type=float
        )
        return value if value > 0 else 27.8

    @staticmethod
    def _validateReplicaPairCount(value):
        """Validate a Replica pair count without accepting coercible values."""
        if isinstance(value, bool) or not isinstance(value, int):
            return 1
        return max(1, min(10, value))

    def _loadReplicaPairCount(self):
        """Load the symmetric Replica pair count from the canonical JSON config."""
        parms = JsonSettings(self.choose_point_click_handler.plot_ts.config_file)
        parms.load(block_key="timeseries settings")
        value = parms.get(["time series plot", "replica pair count"])
        return self._validateReplicaPairCount(value)

    def _reloadReplicaPairCountFromConfig(self):
        """Reload the canonical Replica pair count and synchronize its toolbar view."""
        parms = JsonSettings(self.choose_point_click_handler.plot_ts.config_file)
        parms.load(block_key="timeseries settings")
        value = parms.get(["time series plot", "replica pair count"])
        self.time_series_replica_pair_count = self._validateReplicaPairCount(value)
        self._syncTimeSeriesReplicaControls()

    def _restoreTimeSeriesReplicaState(self):
        """Restore Replica configuration after plotter lifecycle changes."""
        self._reloadReplicaPairCountFromConfig()
        self._applyTimeSeriesReplicaState(refresh=False)

    def _syncTimeSeriesReplicaControls(self):
        """Synchronize toolbar and temporary Settings controls without recursion."""
        toolbar = self.ui.time_series_toolbar
        toolbar.setReplicaEnabled(self.time_series_replica_enabled)
        toolbar.setReplicaInterval(self.time_series_replica_interval_mm)
        toolbar.setReplicaPairCount(self.time_series_replica_pair_count)

    def _applyTimeSeriesReplicaState(self, refresh=True):
        """Apply Replica state and optionally redraw the active plot exactly once."""
        plot = self.choose_point_click_handler.plot_ts
        plot.replicate_flag = self.time_series_replica_enabled
        plot.replicate_value = self.time_series_replica_interval_mm
        plot.parms["time series plot"][
            "replica pair count"
        ] = self.time_series_replica_pair_count
        self._syncTimeSeriesReplicaControls()
        self.settings.setValue(
            "insar_explorer/replica_enabled", self.time_series_replica_enabled
        )
        self.settings.setValue(
            "insar_explorer/replica_interval_mm", self.time_series_replica_interval_mm
        )
        if refresh:
            plot.plotTs(update=True)

    def setTimeSeriesReplicaEnabled(self, enabled):
        """Enable or disable replicas while preserving the selected interval."""
        self.time_series_replica_enabled = bool(enabled)
        self._applyTimeSeriesReplicaState()
        if enabled:
            message = (
                "Replica enabled: time series will be replicated every "
                f"±{self.time_series_replica_interval_mm:.1f} mm."
            )
        else:
            message = "Replica disabled."
        self.msg_signal.emit(message, "i", 0)

    def setTimeSeriesReplicaInterval(self, interval_mm):
        """Store a positive replica interval and redraw only when Replica is active."""
        interval_mm = float(interval_mm)
        if interval_mm <= 0:
            return
        self.time_series_replica_interval_mm = interval_mm
        self._applyTimeSeriesReplicaState(refresh=self.time_series_replica_enabled)
        self.msg_signal.emit(
            f"Replica interval set to ±{interval_mm:.1f} mm.", "i", 0
        )

    def _persistReplicaPairCount(self, pair_count):
        """Persist the validated Replica pair count to the plot configuration."""
        block_key = "timeseries settings"
        parms = JsonSettings(self.choose_point_click_handler.plot_ts.config_file)
        settings_block = parms.load(block_key=block_key)
        settings_block["time series plot"]["replica pair count"]["value"] = pair_count
        parms.save(block_key, settings_block)

    def setTimeSeriesReplicaPairCount(self, pair_count):
        """Persist a symmetric pair count before optionally redrawing Replica."""
        pair_count = self._validateReplicaPairCount(pair_count)
        self._persistReplicaPairCount(pair_count)
        self.time_series_replica_pair_count = pair_count
        self._applyTimeSeriesReplicaState(refresh=self.time_series_replica_enabled)
        self.msg_signal.emit(
            f"Replica pairs set to {self.time_series_replica_pair_count}.", "i", 0
        )

    def handleUiClose(self, visible):
        if not visible:
            self.choose_point_click_handler.clearFeatureHighlight()
            self.choose_point_click_handler.clearReferenceFeatureHighlight()
            self.removeClickTool()
            self.removePolygonDrawingTool(reference=False)
            self.removePolygonDrawingTool(reference=True)
            self.ui.pb_choose_point.setChecked(False)
            self.ui.pb_set_reference.setChecked(False)
            self.ui.pb_choose_polygon.setChecked(False)

    def activatePointSelection(self, status):
        self.ui.pb_set_reference.setChecked(False)
        self.ui.pb_choose_polygon.setChecked(False)
        self.ui.pb_set_reference_polygon.setChecked(False)
        if status:
            self.initializeClickTool()
            self.iface.mapCanvas().setMapTool(self.click_tool)
            self.msg_signal.emit("Click any point on the map to view its time series.", "t", 0)
        else:
            self.removeClickTool()

    def activateReferencePointSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        self.ui.pb_choose_polygon.setChecked(False)
        self.ui.pb_set_reference_polygon.setChecked(False)
        if status:
            self.initializeClickTool()
            self.iface.mapCanvas().setMapTool(self.click_tool)
            self.msg_signal.emit("Click any point on the map to set it as reference.", "t", 0)
        else:
            self.ui.pb_set_reference.setChecked(False)
            self.removeClickTool()

    def activatePolygonSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        self.ui.pb_set_reference.setChecked(False)
        self.ui.pb_set_reference_polygon.setChecked(False)
        if status:
            self.initializePolygonDrawingTool()
            self.msg_signal.emit("Click multiple points to draw polygon; right‑click to close polygon and plot time "
                                 "series.", "t", 0)
        else:
            self.deactivatePolygonDrawingTool(reference=False)

    def activateReferencePolygonSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        self.ui.pb_set_reference.setChecked(False)
        self.ui.pb_choose_polygon.setChecked(False)
        if status:
            self.initializePolygonDrawingTool(reference=True)
            self.msg_signal.emit("Click multiple points to draw reference polygon; right‑click to close polygon.", "t",
                                 0)
        else:
            self.deactivatePolygonDrawingTool(reference=True)

    def resetReferencePoint(self):
        self.choose_point_click_handler.resetReferencePoint()
        self.activateReferencePointSelection(status=False)

        if self.ui.cb_symbol_value_offset_sync_with_ref.isChecked():
            self.ui.sb_symbol_value_offset.setValue(0)
            self.applySymbologyNow()

        self.removePolygonDrawingTool(reference=True)  # remove reference polygon
        self.deactivatePolygonDrawingTool(reference=False)  # deactivate polygon
        self.msg_signal.emit("Reference point has been reset.", "done", 5000)

    def syncOffsetWithReferenceClicked(self, status):
        if status:
            self.syncOffsetWithReference()
            self.msg_signal.emit("Map reference update enabled: map will update when the reference point changes.",
                                 "done", 0)
        else:
            self.msg_signal.emit("Map reference update disabled.", "i", 0)

    def addSelectedLayers(self):
        """
        add selected layers to the list widget
        """
        selected_layers = self.iface.layerTreeView().selectedLayers()
        existing_layers = [self.ui.lw_layers.item(i).text() for i in range(self.ui.lw_layers.count())]

        for layer in selected_layers:
            layer_name = layer.name()
            if layer_name not in existing_layers:
                print(layer_name)
                self.ui.lw_layers.addItem(layer_name)

    def removeSelectedLayers(self):
        """
        remove layers from the list widget
        """
        selected_layers = self.ui.lw_layers.selectedItems()
        for layer in selected_layers:
            self.ui.lw_layers.takeItem(self.ui.lw_layers.row(layer))


    def _initialExportDirectory(self):
        """Return the initial directory used by plot and data export dialogs."""
        saved_path = self.settings.value('insar_explorer/export_directory', '', type=str)
        if saved_path and os.path.isdir(saved_path):
            return saved_path

        home_path = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        if home_path and os.path.isdir(home_path):
            return home_path

        return os.path.expanduser('~')

    def _suggestedExportPath(self, filename):
        """Return a full export path in a usable directory."""
        export_dir = self.last_save_path
        if not export_dir or not os.path.isdir(export_dir):
            export_dir = self._initialExportDirectory()
            self.last_save_path = export_dir
        return os.path.join(export_dir, filename)

    def _rememberExportPath(self, file_path):
        """Remember the last directory used by plot and data export dialogs."""
        export_dir = os.path.dirname(file_path)
        if not export_dir:
            return
        self.last_save_path = export_dir
        self.settings.setValue('insar_explorer/export_directory', export_dir)


    @staticmethod
    def _extensionFromFilter(selected_filter):
        """Return the first file extension advertised by a QFileDialog filter."""
        if not selected_filter:
            return ""

        start = selected_filter.find('*.')
        if start == -1:
            return ""

        start += 1
        end = selected_filter.find(')', start)
        if end == -1:
            end = len(selected_filter)

        extension = selected_filter[start:end].split()[0].strip(';')
        return extension.lower()

    @staticmethod
    def _withExtension(filename, extension):
        """Return filename with extension applied to its suffix."""
        if not extension:
            return filename
        if not extension.startswith('.'):
            extension = f'.{extension}'

        base, _ = os.path.splitext(filename)
        return base + extension

    def _rememberExportFormat(self, settings_key, file_path):
        """Remember the extension used by an export dialog."""
        _, extension = os.path.splitext(file_path)
        if not extension:
            return
        self.settings.setValue(settings_key, extension.lstrip('.').lower())

    def saveTsPlot(self):
        self.msg_signal.emit("", "", 0)

        if self.choose_point_click_handler.plot_ts.current_series() is None:
            self.msg_signal.emit('No time-series plot to export.', 'w', 0)
            return

        plot_extension = self.last_plot_export_format.lower().lstrip('.')
        suggested_name = self._withExtension(self.last_save_ts_name, plot_extension)
        suggested_path = self._suggestedExportPath(suggested_name)
        _, ext = os.path.splitext(suggested_path)

        ext_to_filter = {
            '.png': "PNG (*.png)",
            '.svg': "SVG (*.svg)",
            '.jpg': "JPG (*.jpg)",
        }
        filters = ";;".join(ext_to_filter.values())
        default = ext_to_filter.get(ext.lower(), "PNG (*.png)")

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self.ui,
            "Save plot as image",
            suggested_path,
            filters,
            default,
        )

        if not file_path:
            return

        base, ext = os.path.splitext(file_path)
        selected_extension = self._extensionFromFilter(selected_filter)
        if ext == '' and selected_extension:
            file_path = base + selected_extension
        elif ext == '':
            file_path = base + '.png'

        self._rememberExportPath(file_path)
        self._rememberExportFormat('insar_explorer/plot_export_format', file_path)
        self.last_plot_export_format = os.path.splitext(file_path)[1].lstrip('.').lower()
        self.last_save_ts_name = os.path.basename(file_path)

        self.choose_point_click_handler.plot_ts.savePlotAsImage(file_path)

    def exportTs(self):
        """Export the latest plotted time series to CSV or TXT."""
        self.msg_signal.emit("", "", 0)

        if self.choose_point_click_handler.plot_ts.dates is None:
            self.msg_signal.emit('No time series to export.', 'w', 0)
            return

        ts_extension = self.last_ts_export_format.lower().lstrip('.')
        suggested_name = self._withExtension(self.last_export_ts_name, ts_extension)
        suggested_path = self._suggestedExportPath(suggested_name)
        _, ext = os.path.splitext(suggested_path)

        ext_to_filter = {
            '.csv': "CSV files (*.csv)",
            '.txt': "Text files (*.txt)",
        }
        filters = ";;".join(ext_to_filter.values())
        default = ext_to_filter.get(ext.lower(), "CSV files (*.csv)")

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self.ui,
            "Export time series data",
            suggested_path,
            filters,
            default,
        )

        if not file_path:
            return

        base, ext = os.path.splitext(file_path)
        selected_extension = self._extensionFromFilter(selected_filter)
        if ext == '' and selected_extension:
            file_path = base + selected_extension
        elif ext == '':
            file_path = base + '.csv'

        self.choose_point_click_handler.plot_ts.exportAscii(file_path)

        self._rememberExportPath(file_path)
        self._rememberExportFormat('insar_explorer/ts_export_format', file_path)
        self.last_ts_export_format = os.path.splitext(file_path)[1].lstrip('.').lower()
        self.last_export_ts_name = os.path.basename(file_path)

        self.msg_signal.emit(f'Time series exported: {file_path}', 'done', 3000)

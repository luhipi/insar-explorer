import os

from qgis.gui import QgsMapToolEmitPoint
from PyQt5.QtWidgets import QFileDialog, QMenu, QComboBox
from PyQt5.QtCore import QObject, QTimer, QVariant, pyqtSignal
from PyQt5.QtGui import QIcon, QTransform

from . import map_click_handler as cph
from . import setup_frames
from .map_setting import InsarMap
from .layer_utils import vector_layer as vector_layer_utils
from .about import about as insar_explorer_about
from ..external.setting_manager_ui.setting_ui import SettingsTableDialog
from .drawing_tools.polygon_drawing_tool import PolygonDrawingTool


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
        self.initializeSelection()
        setup_frames.setupTsFrame(self.ui)
        self.insar_map = InsarMap(self.iface)
        self.last_saved_ts_path = "ts_plot.png"
        self.connectUiSignals()
        # make point selection active by default
        self.ui.pb_choose_point.setChecked(True)
        self.activatePointSelection(True)

        # add data range menu
        self.setDataRangeMenu()

        self.iface.currentLayerChanged.connect(self.onLayerChanged)
        self.onLayerChanged()

        self.setVectorFields()

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
            self.insar_map.reset()
            self.setVectorFields()

            layer_type = layer.type()
            is_local_raster = (hasattr(layer, "dataProvider") and getattr(layer.dataProvider(), "name", lambda: "")()
                               in ["gdal"]) #  "ogr"

            if layer_type == layer.VectorLayer:
                self.ui.pb_choose_polygon.setEnabled(True)
                self.ui.pb_set_reference_polygon.setEnabled(True)
            elif layer_type == layer.RasterLayer:
                self.ui.tab_config_panel.setEnabled(False)
                self.ui.pb_choose_polygon.setEnabled(False)
                self.ui.pb_set_reference_polygon.setEnabled(False)

            if layer_type == layer.RasterLayer and not is_local_raster:
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
        self.choose_point_click_handler.choosePointClicked(point=point, layer=None, ref=self.ui.pb_set_reference.isChecked(),
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
        num_chars = max(20, (width - buffer) // avg_char_width)

        info = ""
        warning = "🟡️ "
        error = "🟠 "
        tip = "💡 "
        done = "🟢 "

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
        self.ui.gb_ts_fit.buttonClicked.connect(self.timeseriesPlotFit)
        self.ui.pb_ts_fit_seasonal.clicked.connect(self.seasonalFitClicked)
        self.ui.pb_plot_residuals.toggled.connect(self.residualPlotClicked)
        # Plot setting
        self.ui.gb_y_axis.buttonClicked.connect(self.plotYAxis)
        self.ui.cb_hold_on_plot.toggled.connect(self.holdOnPlot)
        # TS save
        self.ui.pb_ts_save.clicked.connect(self.saveTsPlot)
        # Replica
        self.ui.pb_ts_replica.clicked.connect(self.timeseriesReplica)
        self.ui.sb_ts_replica.valueChanged.connect(self.timeseriesReplica)

        # Setting popup
        self.ui.pb_ts_settings.clicked.connect(self.settingsWidgetPopup)
        # map
        self.connectMapSignals()

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

    def onSettingDialogChanged(self):
        self.choose_point_click_handler.plot_ts.plotTs()

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
            self.msg_signal.emit("Symbology ranges unsynced.", 't', 0)

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
            self.msg_signal.emit("Live symbology enabled: changes will apply immediately.", 't', 0)
        else:
            self.msg_signal.emit("Live symbology disabled.", 't', 0)

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

    def seasonalFitClicked(self, status):
        if status and self.ui.pb_ts_nofit.isChecked():
            self.ui.pb_ts_fit_poly1.setChecked(True)
        self.timeseriesPlotFit()
        self.msg_signal.emit("Seasonal fit enabled: a seasonal component will be added to the selected model.",
                             "i", 0)

    def timeseriesPlotFit(self):
        if self.ui.pb_ts_nofit.isChecked():
            self.ui.pb_ts_fit_seasonal.setChecked(False)
            self.ui.pb_plot_residuals.setChecked(False)

        selected_buttons = [button for button in self.ui.gb_ts_fit.buttons() if
                            button.isChecked()]
        check_box_lookup = {self.ui.pb_ts_nofit: [],
                            self.ui.pb_ts_fit_poly1: "poly-1",
                            self.ui.pb_ts_fit_poly2: "poly-2",
                            self.ui.pb_ts_fit_poly3: "poly-3",
                            self.ui.pb_ts_fit_exp: "exp", }

        if self.ui.pb_ts_nofit.isChecked():
            self.choose_point_click_handler.plot_ts.fit_models = []
            self.msg_signal.emit("No fit model selected.", "i", 0)
        else:
            fit_models = [check_box_lookup[button] for button in selected_buttons]
            self.choose_point_click_handler.plot_ts.fit_models = fit_models
            seasonal_flag = self.ui.pb_ts_fit_seasonal.isChecked()
            self.choose_point_click_handler.plot_ts.fit_seasonal_flag = seasonal_flag
            msg = f"Fit model selected: {', '.join(fit_models)}"
            msg = msg + " Seasonal component will be added." if seasonal_flag else msg
            self.msg_signal.emit(msg, "i", 0)

        self.timeseriesPlotResiduals()

        self.choose_point_click_handler.plot_ts.fitModel()

    def residualPlotClicked(self, status):
        # disable hold on when residuals are plotted
        self.ui.cb_hold_on_plot.setChecked(False)
        if self.ui.pb_plot_residuals.isChecked() and self.ui.pb_ts_nofit.isChecked():
            self.ui.pb_ts_fit_poly1.setChecked(True)
        self.timeseriesPlotFit()
        if status:
            self.msg_signal.emit("Residual plot enabled: measurement − fit.",
                                 "i", 0)
        else:
            self.msg_signal.emit("Residual plot disabled.", "i", 0)

    def timeseriesPlotResiduals(self):
        self.choose_point_click_handler.plot_ts.plot_residuals_flag = (self.ui.pb_plot_residuals.isChecked()
                                                                       and not self.ui.pb_ts_nofit.isChecked())
        self.choose_point_click_handler.plot_ts.plotTs()

    def holdOnPlot(self, status):
        self.choose_point_click_handler.plot_ts.hold_on_flag = self.ui.cb_hold_on_plot.isChecked()
        if status:
            self.msg_signal.emit("Hold on plot enabled: new plots will be added to the existing plot.",
                                 "i", 0)
        else:
            self.msg_signal.emit("Hold on plot disabled.",
                                 "i", 0)


    def plotYAxis(self):
        if self.ui.cb_y_from_data.isChecked():
            self.choose_point_click_handler.plot_ts.plot_y_axis = "from_data"
            self.msg_signal.emit("Y-axis range set from data.", "i", 0)
        elif self.ui.cb_y_symmetric.isChecked():
            self.choose_point_click_handler.plot_ts.plot_y_axis = "symmetric"
            self.msg_signal.emit("Y-axis range set symmetric.", "i", 0)
        elif self.ui.cb_y_adaptive.isChecked():
            self.choose_point_click_handler.plot_ts.plot_y_axis = "adaptive"
            self.msg_signal.emit("Y-axis range set adaptively: less range change when plotting new time series.", "i",
                                 0)

        self.choose_point_click_handler.plot_ts.plotTs()

    def timeseriesReplica(self):
        if self.ui.pb_ts_replica.isChecked():
            self.choose_point_click_handler.plot_ts.replicate_flag = True
            replicate_value = int(self.ui.sb_ts_replica.text())
            self.choose_point_click_handler.plot_ts.replicate_value = replicate_value
            self.msg_signal.emit(f"Replica enabled: time series will be replicated every ±{replicate_value} units.",
                                 "i", 0)
        else:
            self.choose_point_click_handler.plot_ts.replicate_flag = False
            self.msg_signal.emit("Replica disabled.", "i", 0)
        self.choose_point_click_handler.plot_ts.plotTs()

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
            self.msg_signal.emit("Click multiple points to draw polygon; right‑click to close and plot its time series."
                                 , "t", 0)
        else:
            self.deactivatePolygonDrawingTool(reference=False)

    def activateReferencePolygonSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        self.ui.pb_set_reference.setChecked(False)
        self.ui.pb_choose_polygon.setChecked(False)
        if status:
            self.initializePolygonDrawingTool(reference=True)
            self.msg_signal.emit("Click multiple points to draw reference polygon; right‑click to close it."
                                 , "t", 0)
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
                                 "i", 0)
        else:
            self.msg_signal.emit("Map reference update disabled."
                                 , "i", 0)

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

    def saveTsPlot(self):
        self.msg_signal.emit("", "", 0)
        file_path, _ = QFileDialog.getSaveFileName(
            self.ui,
            "Save plot as image",
            self.last_saved_ts_path,
            "Images (*.png *.jpg *.svg *.pdf)"
        )

        if file_path:
            self.last_saved_ts_path = file_path
            self.choose_point_click_handler.plot_ts.savePlotAsImage(file_path)

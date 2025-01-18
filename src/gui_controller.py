import os

from qgis.gui import QgsMapToolEmitPoint
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QObject, QTimer

from . import map_click_handler as cph
from . import setup_frames
from .map_setting import InsarMap
from .setting_manager_ui.setting_ui import SettingsTableDialog
from .drawing_tools.polygon_drawing_tool import PolygonDrawingTool


class GuiController(QObject):
    def __init__(self, plugin):
        super().__init__()
        self.iface = plugin.iface
        self.ui = plugin.dockwidget
        self.choose_point_click_handler = cph.ClickHandler(plugin)
        # self.choose_polygon_click_handler = cph.ClickHandler(plugin)
        self.click_tool = None #plugin.click_tool
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

        self.iface.currentLayerChanged.connect(self.onLayerChanged)

    def initializeSelection(self):
        if self.selection_type == "point":
            self.initializeClickTool()
        elif self.selection_type == "polygon":
            self.initializePolygonDrawingTool()
        elif self.selection_type == "reference polygon":
            self.initializePolygonDrawingTool(reference=True)

    def onLayerChanged(self, layer):
        """Reset the click handler and the map when the active layer changes."""
        if layer:
            self.choose_point_click_handler.reset()
            self.insar_map.reset()

    def initializeClickTool(self):
        if not self.click_tool:
            self.click_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
            # self.click_tool.canvasClicked.connect(lambda point: self.choose_point_click_handler.choosePointClicked(point))
            self.click_tool.canvasClicked.connect(lambda point: self.choose_point_click_handler.choosePointClicked(
                                                  point=point, layer=None, ref=self.ui.pb_set_reference.isChecked()))

    def removeClickTool(self):
        self.iface.mapCanvas().unsetMapTool(self.click_tool)
        self.click_tool = None

    def initializePolygonDrawingTool(self, reference=False):
        if not reference:
            if not self.drawing_tool:
                self.drawing_tool = (
                    PolygonDrawingTool(self.iface.mapCanvas(), callback=self.polygonDrawnCallback,
                                       start_callback=self.choose_point_click_handler.clearFeatureHighlight))
            self.iface.mapCanvas().setMapTool(self.drawing_tool)
        else:
            if not self.drawing_tool_reference:
                self.drawing_tool_reference = (
                    PolygonDrawingTool(self.iface.mapCanvas(), callback=self.polygonDrawnCallback,
                                       start_callback=self.choose_point_click_handler.clearReferenceFeatureHighlight))
                self.drawing_tool_reference.polygon_marker.setStyle(color=(255, 100, 100, 80))
            self.iface.mapCanvas().setMapTool(self.drawing_tool_reference)

    def removePolygonDrawingTool(self, reference=False):
        if not reference and self.drawing_tool:
            self.iface.mapCanvas().unsetMapTool(self.drawing_tool)
            if self.drawing_tool:
                self.drawing_tool.clear()
            self.drawing_tool = None
        elif reference and self.drawing_tool_reference:
            self.iface.mapCanvas().unsetMapTool(self.drawing_tool_reference)
            if self.drawing_tool_reference:
                self.drawing_tool_reference.clear()
            self.drawing_tool_reference = None

    def polygonDrawnCallback(self, polygon):
        self.choose_point_click_handler.choosePolygonDrawn(polygon=polygon, ref=self.ui.pb_set_reference_polygon.isChecked())

    def connectUiSignals(self):
        self.ui.visibilityChanged.connect(self.handleUiClose)
        # self.ui.pb_add_layers.clicked.connect(self.addSelectedLayers)
        # self.ui.pb_remove_layers.clicked.connect(self.removeSelectedLayers)
        self.connectTimeseriesSignals()
        self.connectMapSignals()

    def connectTimeseriesSignals(self):
        self.ui.pb_choose_point.clicked.connect(self.activatePointSelection)
        self.ui.pb_set_reference.clicked.connect(self.activateReferencePointSelection)
        self.ui.pb_reset_reference.clicked.connect(self.resetReferencePoint)
        self.ui.pb_choose_polygon.clicked.connect(self.activatePolygonSelection)
        self.ui.pb_set_reference_polygon.clicked.connect(self.activateReferencePolygonSelection)
        # TS fit handler
        self.ui.gb_ts_fit.buttonClicked.connect(self.timeseriesPlotFit)
        self.ui.pb_ts_fit_seasonal.clicked.connect(self.timeseriesPlotFit)
        self.ui.cb_plot_residuals.toggled.connect(self.timeseriesPlotResiduals)
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
        self.ui.pb_symbology.clicked.connect(self.applySymbology)
        self.ui.sb_symbol_lower_range.valueChanged.connect(self.setSymbologyLowerRange)
        self.ui.sb_symbol_upper_range.valueChanged.connect(self.setSymbologyUpperRange)
        self.ui.cb_symbol_range_sync.clicked.connect(self.setSymbologyLowerRange)
        # get range from data
        self.ui.pb_range_from_data.clicked.connect(self.setSymbologyRangeFromData)
        self.ui.pb_range_from_data_1std.clicked.connect(self.setSymbologyRangeFromData)
        self.ui.pb_range_from_data_3std.clicked.connect(self.setSymbologyRangeFromData)
        #
        self.ui.sb_symbol_classes.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_size.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_opacity.valueChanged.connect(self.applyLiveSymbology)
        self.ui.cb_symbology_live.toggled.connect(self.applyLiveSymbology)
        self.ui.cmb_colormap.currentIndexChanged.connect(self.applyLiveSymbology)
        self.ui.cb_colormap_reverse.toggled.connect(self.applyLiveSymbology)

    def settingsWidgetPopup(self):
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

    def setSymbologyRangeFromData(self):
        button = self.sender()
        if button == self.ui.pb_range_from_data:
            message = self.insar_map.setSymbologyRangeFromData()
        elif button == self.ui.pb_range_from_data_1std:
            message = self.insar_map.setSymbologyRangeFromData(n_std=1)
        elif button == self.ui.pb_range_from_data_3std:
            message = self.insar_map.setSymbologyRangeFromData(n_std=3)

        self.ui.lb_msg_bar.setText(message)
        self.ui.cb_symbol_range_sync.setChecked(False)
        self.ui.sb_symbol_lower_range.setValue(self.insar_map.min_value)
        self.ui.sb_symbol_upper_range.setValue(self.insar_map.max_value)

    def applyLiveSymbology(self):
        if self.ui.cb_symbology_live.isChecked():
            QTimer.singleShot(0, self.applySymbology)

    def applySymbology(self):
        self.insar_map.min_value = float(self.ui.sb_symbol_lower_range.value())
        self.insar_map.max_value = float(self.ui.sb_symbol_upper_range.value())
        self.insar_map.num_classes = int(self.ui.sb_symbol_classes.value())
        self.insar_map.alpha = float(self.ui.sb_symbol_opacity.value())/100
        self.insar_map.symbol_size = float(self.ui.sb_symbol_size.value())
        self.insar_map.color_ramp_name = self.ui.cmb_colormap.currentText()
        self.insar_map.color_ramp_reverse_flag = self.ui.cb_colormap_reverse.isChecked()
        message = self.insar_map.setSymbology()
        self.ui.lb_msg_bar.setText(message)

    def timeseriesPlotFit(self):
        selected_buttons = [button for button in self.ui.gb_ts_fit.buttons() if
                            button.isChecked()]
        check_box_lookup = {self.ui.pb_ts_nofit: [],
                            self.ui.pb_ts_fit_poly1: "poly-1",
                            self.ui.pb_ts_fit_poly2: "poly-2",
                            self.ui.pb_ts_fit_poly3: "poly-3",
                            self.ui.pb_ts_fit_exp: "exp", }

        if self.ui.pb_ts_nofit.isChecked():
            self.choose_point_click_handler.plot_ts.fit_models = []
        else:
            self.choose_point_click_handler.plot_ts.fit_models = [check_box_lookup[button] for button in
                                                                  selected_buttons]

        self.choose_point_click_handler.plot_ts.fit_seasonal_flag = self.ui.pb_ts_fit_seasonal.isChecked()
        self.timeseriesPlotResiduals()

        self.choose_point_click_handler.plot_ts.fitModel()

    def timeseriesPlotResiduals(self):
        self.choose_point_click_handler.plot_ts.plot_residuals_flag = (
                self.ui.cb_plot_residuals.isChecked() and not self.ui.pb_ts_nofit.isChecked())
        self.choose_point_click_handler.plot_ts.plotTs()

    def timeseriesReplica(self):
        if self.ui.pb_ts_replica.isChecked():
            self.choose_point_click_handler.plot_ts.replicate_flag = True
            self.choose_point_click_handler.plot_ts.replicate_value = int(self.ui.sb_ts_replica.text())
        else:
            self.choose_point_click_handler.plot_ts.replicate_flag = False
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
        else:
            self.removeClickTool()

    def activateReferencePointSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        self.ui.pb_choose_polygon.setChecked(False)
        self.ui.pb_set_reference_polygon.setChecked(False)
        if status:
            self.initializeClickTool()
            self.iface.mapCanvas().setMapTool(self.click_tool)
        else:
            self.ui.pb_set_reference.setChecked(False)
            self.removeClickTool()

    def activatePolygonSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        self.ui.pb_set_reference.setChecked(False)
        self.ui.pb_set_reference_polygon.setChecked(False)
        if status:
            self.initializePolygonDrawingTool()
        else:
            self.removePolygonDrawingTool()

    def activateReferencePolygonSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        self.ui.pb_set_reference.setChecked(False)
        self.ui.pb_choose_polygon.setChecked(False)
        if status:
            self.initializePolygonDrawingTool(reference=True)
        else:
            self.removePolygonDrawingTool(reference=True)

    def resetReferencePoint(self):
        self.choose_point_click_handler.resetReferencePoint()
        self.activateReferencePointSelection(status=False)

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
        file_path, _ = QFileDialog.getSaveFileName(
            self.ui,
            "Save plot as image",
            self.last_saved_ts_path,
            "Images (*.png *.jpg *.svg *.pdf)"
        )

        if file_path:
            self.last_saved_ts_path = file_path
            self.choose_point_click_handler.plot_ts.savePlotAsImage(file_path)
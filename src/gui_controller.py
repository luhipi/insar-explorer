from qgis.gui import QgsMapToolEmitPoint
from . import map_click_handler as cph
from . import setup_frames
from .map_setting import InsarMap


class GuiController():
    def __init__(self, plugin):
        self.iface = plugin.iface
        self.ui = plugin.dockwidget
        self.choose_point_click_handler = cph.TSClickHandler(plugin)
        self.click_tool = None #plugin.click_tool
        self.initializeClickTool()
        setup_frames.setupTsFrame(self.ui)
        self.insar_map = InsarMap(self.iface)
        self.connectUiSignals()
        # make point selection active by default
        self.ui.pb_choose_point.setChecked(True)
        self.activatePointSelection(True)

    def initializeClickTool(self):
        if not self.click_tool:
            self.click_tool = QgsMapToolEmitPoint(self.iface.mapCanvas())
            # self.click_tool.canvasClicked.connect(lambda point: self.choose_point_click_handler.choosePointClicked(point))
            self.click_tool.canvasClicked.connect(lambda point: self.choose_point_click_handler.choosePointClicked(
                                                  point, self.ui.pb_set_reference.isChecked()))

    def removeClickTool(self):
        self.iface.mapCanvas().unsetMapTool(self.click_tool)
        self.click_tool = None

    def connectUiSignals(self):
        self.ui.visibilityChanged.connect(self.handleUiClose)
        self.ui.pb_choose_point.clicked.connect(self.activatePointSelection)
        self.ui.pb_set_reference.clicked.connect(self.activateReferencePointSelection)
        self.ui.pb_reset_reference.clicked.connect(self.resetReferencePoint)
        # self.ui.pb_add_layers.clicked.connect(self.addSelectedLayers)
        # self.ui.pb_remove_layers.clicked.connect(self.removeSelectedLayers)
        # TS fit handler
        self.ui.gb_ts_fit.buttonClicked.connect(self.timeseriesPlotFit)
        self.ui.pb_ts_fit_seasonal.clicked.connect(self.timeseriesPlotFit)
        # Replica
        self.ui.pb_ts_replica.clicked.connect(self.timeseriesReplica)
        self.ui.sb_ts_replica.valueChanged.connect(self.timeseriesReplica)
        # map
        self.connectMapSignals()

    def connectMapSignals(self):
        self.ui.pb_symbology.clicked.connect(self.applySymbology)
        self.ui.sb_symbol_lower_range.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_upper_range.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_size.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_opacity.valueChanged.connect(self.applyLiveSymbology)
        self.ui.cb_symbology_live.toggled.connect(self.applyLiveSymbology)

    def applyLiveSymbology(self):
        if self.ui.cb_symbology_live.isChecked():
            self.applySymbology()

    def applySymbology(self):
        self.insar_map.min_value = float(self.ui.sb_symbol_lower_range.value())
        self.insar_map.max_value = float(self.ui.sb_symbol_upper_range.value())
        self.insar_map.alpha = float(self.ui.sb_symbol_opacity.value())/100
        self.insar_map.symbol_size = float(self.ui.sb_symbol_size.value())
        self.insar_map.setSymbology()

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

        self.ui.te_info.setPlainText(f"Selected models: {self.choose_point_click_handler.plot_ts.fit_models}")
        self.choose_point_click_handler.plot_ts.fit_seasonal_flag = self.ui.pb_ts_fit_seasonal.isChecked()

        self.choose_point_click_handler.plot_ts.fitModel()

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
            self.ui.pb_choose_point.setChecked(False)
            self.ui.pb_set_reference.setChecked(False)

    def activatePointSelection(self, status):
        self.ui.pb_set_reference.setChecked(False)
        if status:
            self.initializeClickTool()
            self.iface.mapCanvas().setMapTool(self.click_tool)
        else:
            self.removeClickTool()

    def activateReferencePointSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        if status:
            self.initializeClickTool()
            self.iface.mapCanvas().setMapTool(self.click_tool)
        else:
            self.ui.pb_set_reference.setChecked(False)
            self.removeClickTool()

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

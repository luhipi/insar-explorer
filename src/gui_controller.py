from qgis.gui import QgsMapToolEmitPoint
from . import map_click_handler as cph
from . import setup_frames


class GuiController():
    def __init__(self, plugin):
        self.iface = plugin.iface
        self.ui = plugin.dockwidget
        self.choose_point_click_handler = cph.TSClickHandler(plugin)
        self.click_tool = None #plugin.click_tool
        self.initializeClickTool()
        setup_frames.setupTsFrame(self.ui)
        self.connectUiSignals()

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
        self.ui.pb_add_layers.clicked.connect(self.addSelectedLayers)
        self.ui.pb_remove_layers.clicked.connect(self.removeSelectedLayers)

    def handleUiClose(self, visible):
        if not visible:
            self.choose_point_click_handler.clearFeatureHighlight()
            self.choose_point_click_handler.clearReferenceFeatureHighlight()
            self.removeClickTool()
            self.ui.pb_choose_point.setChecked(False)

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
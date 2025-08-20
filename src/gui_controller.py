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


class GuiController(QObject):
    msg_signal = pyqtSignal(str, str, int)
    def __init__(self, plugin):
        super().__init__()
        self.iface = plugin.iface
        self.ui = plugin.dockwidget
        self.choose_point_click_handler = cph.TSClickHandler(plugin, msg_signal=self.msg_signal)
        self.click_tool = None  # plugin.click_tool
        self.initializeClickTool()
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

        self.setVectorFields()

    def onLayerChanged(self, layer):
        if layer:
            self.choose_point_click_handler.reset()
            self.insar_map.reset()
            self.setVectorFields()

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
        self.msg_signal.emit("", 'i', 0)
        self.choose_point_click_handler.choosePointClicked(point=point, layer=None, ref=self.ui.pb_set_reference.isChecked())

        if self.ui.pb_set_reference.isChecked():
            if self.ui.cb_symbol_value_offset_sync_with_ref.isChecked():
                self.insar_map.offset_value =self.choose_point_click_handler.map_reference_clicked_value
                self.ui.sb_symbol_value_offset.setValue(self.choose_point_click_handler.map_reference_clicked_value)

    def removeClickTool(self):
        self.iface.mapCanvas().unsetMapTool(self.click_tool)
        self.click_tool = None

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

        info = "ℹ "  # U+2139
        warning = "⚠ "  # U+26A0
        error = "❌ "  # U+274C
        tip = "💡 "  # U+1F4A1

        if v == 'w':
            self.ui.lb_msg_bar.setStyleSheet("color: black; background-color: #FFF3E0;")
            message = warning + str(message)
        elif v == 'e':
            self.ui.lb_msg_bar.setStyleSheet("color: black; background-color: #FFEBEE;")
            message = error + str(message)
        elif v == 'i':
            self.ui.lb_msg_bar.setStyleSheet("color: black; background-color: transparent;")
            message = info + str(message)
        elif v == 't':
            self.ui.lb_msg_bar.setStyleSheet("color: black; background-color: transparent;")
            message = tip + str(message)
        else:
            self.ui.lb_msg_bar.setStyleSheet("color: black; background-color: transparent;")
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

    def connectMapSignals(self):
        self.ui.cb_select_field.currentTextChanged.connect(self.selectVectorFieldChanged)
        self.ui.pb_symbology.clicked.connect(self.applySymbology)
        self.ui.sb_symbol_lower_range.valueChanged.connect(self.setSymbologyLowerRange)
        self.ui.sb_symbol_upper_range.valueChanged.connect(self.setSymbologyUpperRange)
        self.ui.cb_symbol_range_sync.clicked.connect(self.setSymbologyLowerRange)
        self.ui.sb_symbol_value_offset.valueChanged.connect(self.setSymbologyOffset)
        self.ui.sb_symbol_classes.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_size.valueChanged.connect(self.applyLiveSymbology)
        self.ui.sb_symbol_opacity.valueChanged.connect(self.applyLiveSymbology)
        self.ui.pb_symbology_live.toggled.connect(self.applyLiveSymbology)
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

    def setSymbologyOffset(self):
        self.insar_map.offset_value = self.ui.sb_symbol_value_offset.value()
        self.applyLiveSymbology()

    def setSymbologyRangeFromData(self):
        button = self.sender()
        if button.text() == "Range from data":
            message = self.insar_map.setSymbologyRangeFromData()
        elif button.text() == "1xStd":
            message = self.insar_map.setSymbologyRangeFromData(n_std=1)
        elif button.text() == "2xStd":
            message = self.insar_map.setSymbologyRangeFromData(n_std=2)
        elif button.text() == "3xStd":
            message = self.insar_map.setSymbologyRangeFromData(n_std=3)

        self.msg_signal.emit(message, 'i', 5000)
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
        self.msg_signal.emit(message, 'i', 5000)

    def colormapReverseClicked(self):
        self.flipComboBoxIcons(self.ui.cmb_colormap)
        self.insar_map.color_ramp_reverse_flag = self.ui.pb_colormap_reverse.isChecked()
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
        else:
            self.choose_point_click_handler.plot_ts.fit_models = [check_box_lookup[button] for button in
                                                                  selected_buttons]

        self.choose_point_click_handler.plot_ts.fit_seasonal_flag = self.ui.pb_ts_fit_seasonal.isChecked()
        self.timeseriesPlotResiduals()

        self.choose_point_click_handler.plot_ts.fitModel()

    def residualPlotClicked(self):
        # disable hold on when residuals are plotted
        self.ui.cb_hold_on_plot.setChecked(False)
        if self.ui.pb_plot_residuals.isChecked() and self.ui.pb_ts_nofit.isChecked():
            self.ui.pb_ts_fit_poly1.setChecked(True)
        self.timeseriesPlotFit()

    def timeseriesPlotResiduals(self):
        self.choose_point_click_handler.plot_ts.plot_residuals_flag = (self.ui.pb_plot_residuals.isChecked()
                                                                       and not self.ui.pb_ts_nofit.isChecked())
        self.choose_point_click_handler.plot_ts.plotTs()

    def holdOnPlot(self):
        self.choose_point_click_handler.plot_ts.hold_on_flag = self.ui.cb_hold_on_plot.isChecked()

    def plotYAxis(self):
        if self.ui.cb_y_from_data.isChecked():
            self.choose_point_click_handler.plot_ts.plot_y_axis = "from_data"
        elif self.ui.cb_y_symmetric.isChecked():
            self.choose_point_click_handler.plot_ts.plot_y_axis = "symmetric"
        elif self.ui.cb_y_adaptive.isChecked():
            self.choose_point_click_handler.plot_ts.plot_y_axis = "adaptive"

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
            self.ui.pb_choose_point.setChecked(False)
            self.ui.pb_set_reference.setChecked(False)

    def activatePointSelection(self, status):
        self.ui.pb_set_reference.setChecked(False)
        if status:
            self.initializeClickTool()
            self.iface.mapCanvas().setMapTool(self.click_tool)
            self.msg_signal.emit("Click on the map to select a point and plot its time series.", 't', 5000)
        else:
            self.removeClickTool()

    def activateReferencePointSelection(self, status):
        self.ui.pb_choose_point.setChecked(False)
        if status:
            self.initializeClickTool()
            self.iface.mapCanvas().setMapTool(self.click_tool)
            self.msg_signal.emit("Click on the map to select the reference point for the time series.", 't', 5000)
        else:
            self.ui.pb_set_reference.setChecked(False)
            self.removeClickTool()

    def resetReferencePoint(self):
        self.choose_point_click_handler.resetReferencePoint()
        self.activateReferencePointSelection(status=False)
        if self.ui.cb_symbol_value_offset_sync_with_ref.isChecked():
            self.ui.sb_symbol_value_offset.setValue(0)
            self.applySymbologyNow()
        self.msg_signal.emit("Reference point has been reset.", 'i', 5000)

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

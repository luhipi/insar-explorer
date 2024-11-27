import numpy as np
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsGraduatedSymbolRenderer, QgsRendererRange, QgsSymbol
from qgis.core import QgsRasterShader, QgsColorRampShader, QgsSingleBandPseudoColorRenderer


from . import color_maps
from . import layer_utils

class velocity():
    def __init__(self):
        self.min_value = None
        self.max_value = None
        self.mean_value = None
        self.std_value = None

class InsarMap:
    def __init__(self, iface):
        self.iface = iface
        self.symbol_size = 1
        self.min_value = -5
        self.max_value = 5
        self.data_min = None
        self.data_max = None
        self.data_mean = None
        self.data_stdv = None
        self.stroke_width = 0.01
        self.alpha = 0.9
        self.num_classes = 9
        self.color_ramp_name = 'Roma'
        self.color_ramp_reverse_flag = False
        self.data_type = "vector"

    def setSymbologyRangeFromData(self, layer=None, n_std=None):
        if not layer:
            layer = self.iface.activeLayer()

        status_vector, message = layer_utils.checkVectorLayer(layer)
        status_raster, message = layer_utils.checkGmtsarLayer(layer)
        if status_vector:
            self.data_type = "vector"
            self.getDataRangeFromVectorLayer(layer, n_std)
        elif status_raster:
            self.data_type = "raster"
            self.getDataRangeFromRasterLayer(layer, n_std)
        else:
            message = '<span style="color:red;">Invalid Layer: Please select a valid layer.</span>'
            return message

    def getDataRangeFromVectorLayer(self, layer, n_std=None):
        field_name, message = layer_utils.checkVectorLayerVelocity(layer)
        if field_name is None:
            return message

        if n_std is None:
            if self.data_min is None or self.data_max is None:
                min_max = layer.minimumAndMaximumValue(layer.fields().indexFromName(field_name))
                self.data_min, self.data_max = min_max
                if self.data_min is None or self.data_max is None:
                    values = [feature[field_name] for feature in layer.getFeatures() if feature[field_name] is not None]
                    self.data_min = np.nanmin(values)
                    self.data_max = np.nanmax(values)

            self.min_value = self.data_min
            self.max_value = self.data_max
        else:
            if self.data_mean is None or self.data_stdv is None:
                values = [feature[field_name] for feature in layer.getFeatures() if feature[field_name] is not None]
                self.data_mean = np.nanmean(values)
                self.data_stdv = np.nanstd(values)
            self.min_value = self.data_mean - n_std * self.data_stdv
            self.max_value = self.data_mean + n_std * self.data_stdv

        return ""

    def getDataRangeFromRasterLayer(self, layer, n_std=None):
        if n_std is None:
            if self.data_min is None or self.data_max is None:
                self.data_min = layer.dataProvider().bandStatistics(1).minimumValue
                self.data_max = layer.dataProvider().bandStatistics(1).maximumValue
            self.min_value = self.data_min
            self.max_value = self.data_max
        else:
            if self.data_mean is None or self.data_stdv is None:
                self.data_mean = layer.dataProvider().bandStatistics(1).mean
                self.data_stdv = layer.dataProvider().bandStatistics(1).stdDev
            self.min_value = self.data_mean - n_std * self.data_stdv
            self.max_value = self.data_mean + n_std * self.data_stdv

        return ""

    def setSymbology(self, layer=None, color_ramp_name=None):

        if not color_ramp_name:
            color_ramp_name = self.color_ramp_name

        if not layer:
            layer = self.iface.activeLayer()

        status_vector, message = layer_utils.checkVectorLayer(layer)
        status_raster, message = layer_utils.checkGmtsarLayer(layer)
        if (status_vector and status_raster) is False:
            message = '<span style="color:red;">Could not set the symbology. Check layer validity.</span>'
            return message

        if status_vector or status_raster:
            interval = (self.max_value - self.min_value) / self.num_classes

            if color_ramp_name == 'Turbo':
                color_ramp = color_maps.Turbo()
            if color_ramp_name == 'Roma':
                color_ramp = color_maps.Roma()
            if color_ramp_name == 'Vik':
                color_ramp = color_maps.Vik()

            if self.color_ramp_reverse_flag:
                color_ramp.reverse()

            max_length = max(len(f"{self.min_value:.2f}"), len(f"{self.max_value:.2f}"))

        if status_vector:
            self.setSymbologyVector(layer, interval, max_length, color_ramp)
            return ""
        elif status_raster:
            self.setSymbologyRaster(layer, interval, max_length, color_ramp)
            return ""
        else:
            message = '<span style="color:red;">Could not set the symbology. Check layer validity.</span>'
            return message

    def setSymbologyRaster(self, layer, interval, max_length, color_ramp):

        shader = QgsRasterShader()
        color_ramp_shader = QgsColorRampShader()
        color_ramp_shader.setColorRampType(QgsColorRampShader.Interpolated)

        color_ramp_items = []
        for i in range(self.num_classes):
            value = self.min_value + i * interval
            color_ratio = float(i) / (self.num_classes - 1)
            color = color_ramp.getColor(color_ratio)
            color.setAlphaF(self.alpha)
            color_ramp_items.append(QgsColorRampShader.ColorRampItem(value, color))

        color_ramp_shader.setColorRampItemList(color_ramp_items)
        shader.setRasterShaderFunction(color_ramp_shader)

        renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        self.iface.mapCanvas().refresh()

    def setSymbologyVector(self, layer, interval, max_length, color_ramp):

        ranges = []
        for i in range(self.num_classes):
            lower = self.min_value + i * interval
            upper = lower + interval
            label = f"{lower:>{max_length}.2f}\t-\t{upper:<{max_length}.2f}"

            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            color_ratio = float(i) / (self.num_classes - 1)
            color = color_ramp.getColor(color_ratio)
            color.setAlphaF(self.alpha)
            symbol.setColor(color)
            symbol.setSize(self.symbol_size)
            symbol.symbolLayer(0).setStrokeWidth(self.stroke_width)
            symbol.symbolLayer(0).setStrokeColor(QColor("gray"))

            if i == 0:
                lower = float('-inf')
            if i == self.num_classes - 1:
                upper = float('inf')

            range_item = QgsRendererRange(lower, upper, symbol, label)
            ranges.append(range_item)

        field_name, message = layer_utils.checkVectorLayerVelocity(layer)
        if field_name is None:
            return message
        else:
            renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
            # renderer.setMode(QgsGraduatedSymbolRenderer.Custom)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        self.iface.mapCanvas().refresh()

        return ""

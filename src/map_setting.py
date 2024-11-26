from qgis.PyQt.QtGui import QColor
from qgis.core import QgsGraduatedSymbolRenderer, QgsRendererRange, QgsSymbol
import numpy as np

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

    def setSymbologyRangeFromData(self, layer=None, n_std=None):
        if not layer:
            layer = self.iface.activeLayer()

        status, message = layer_utils.checkVectorLayer(layer)
        if status is False:
            return message

        field_name, message = layer_utils.checkVectorLayerVelocity(layer)
        if field_name is None:
            return message

        if n_std is None:
            if self.data_min is None or self.data_max is None:
                min_max = layer.minimumAndMaximumValue(layer.fields().indexFromName(field_name))
                self.data_min, self.data_max = min_max
            self.min_value = self.data_min
            self.max_value = self.data_max
        else:
            if self.data_mean is None or self.data_stdv is None:
                values = [feature[field_name] for feature in layer.getFeatures() if feature[field_name] is not None]
                self.data_mean = np.mean(values)
                self.data_stdv = np.std(values)
            self.min_value = self.data_mean - n_std * self.data_stdv
            self.max_value = self.data_mean + n_std * self.data_stdv

        return ""

    def setSymbology(self, layer=None, color_ramp_name=None):

        if not color_ramp_name:
            color_ramp_name = self.color_ramp_name

        if not layer:
            layer = self.iface.activeLayer()

        status, message = layer_utils.checkVectorLayer(layer)
        if status is False:
            return message

        interval = (self.max_value - self.min_value) / self.num_classes

        if color_ramp_name == 'Turbo':
            color_ramp = color_maps.Turbo()
        if color_ramp_name == 'Roma':
            color_ramp = color_maps.Roma()
        if color_ramp_name == 'Vik':
            color_ramp = color_maps.Vik()

        if self.color_ramp_reverse_flag:
            color_ramp.reverse()

        ranges = []

        max_length = max(len(f"{self.min_value:.2f}"), len(f"{self.max_value:.2f}"))

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

        # lower_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        # color = color_ramp.getColor(0)
        # color.setAlphaF(self.alpha)
        # lower_symbol.setColor(color)
        # lower_symbol.setSize(self.symbol_size)
        # lower_symbol.symbolLayer(0).setStrokeWidth(self.stroke_width)
        # lower_symbol.symbolLayer(0).setStrokeColor(QColor("gray"))
        # lower_range = QgsRendererRange(float('-inf'), self.min_value, lower_symbol, f"< {self.min_value:.2f}")
        # ranges.insert(0, lower_range)
        #
        # upper_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        # color = color_ramp.getColor(1)
        # color.setAlphaF(self.alpha)
        # upper_symbol.setColor(color)
        # upper_symbol.setSize(self.symbol_size)
        # upper_symbol.symbolLayer(0).setStrokeWidth(self.stroke_width)
        # upper_symbol.symbolLayer(0).setStrokeColor(QColor("gray"))
        # upper_range = QgsRendererRange(self.max_value, float('inf'), upper_symbol, f"> {self.max_value:.2f}")
        # ranges.append(upper_range)

        # TODO: add support for different processors
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

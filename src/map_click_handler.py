import os

from qgis.PyQt.QtWidgets import QMessageBox, QApplication
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsPointXY, QgsGeometry, QgsMapLayer, QgsRectangle, QgsFeatureRequest, QgsSettings, Qgis, QgsFeature
from qgis.gui import QgsHighlight
from PyQt5.QtGui import QCursor

import numpy as np
import re
from datetime import datetime

from osgeo import gdal

from . import plot_timeseries as pts
from .layer_utils import vector_layer as vector_layer_utils
from .layer_utils import gmtsar_layer as gmtsar_layer_utils


class MapClickHandler:
    """
    A class to handle map click events

    Attributes:
        ui: The user interface object of the plugin.
        iface: The QGIS interface object.
        highlight: The QgsHighlight object used to highlight selected features.

    """
    def __init__(self, plugin):
        self.ui = plugin.dockwidget
        self.iface = plugin.iface
        self.highlight = None
        self.reference_highlight = None

    def identifyClickedFeatureID(self, point: QgsPointXY, layer: QgsMapLayer = None) -> int:
        """
        Identify the closest feature to the clicked point
        :param point: QgsPointXY
        :param layer: QgsMapLayer
        :return: closest feature ID
        """
        if not layer:
            layer = self.iface.activeLayer()

        status, message = vector_layer_utils.checkVectorLayer(layer)
        if status is False:
            self.ui.lb_msg_bar.setText(message)
            return

        closest_feature_id = self.findFeatureAtPoint(layer, point, self.iface.mapCanvas(),
                                                     only_the_closest_one=True, only_ids=True)

        if closest_feature_id:
            self.ui.lb_msg_bar.setText(f"")
        else:
            self.ui.lb_msg_bar.setText("Identify Result: No nearby point found. Select another point.")

        return closest_feature_id

    def identifyClickedFeature(self, point: QgsPointXY, layer: QgsMapLayer = None, ref=False) -> QgsGeometry:
        """
        Identify the closest feature to the clicked point and display its attributes
        :param point: QgsPointXY
        :param layer: QgsMapLayer
        :param ref: bool
        :return: closest feature
        """
        if not layer:
            layer = self.iface.activeLayer()
        closest_feature_id = self.identifyClickedFeatureID(point, layer)

        if not ref:
            self.clearFeatureHighlight()
        else:
            self.clearReferenceFeatureHighlight()

        closest_feature = None
        if closest_feature_id:
            closest_feature = layer.getFeature(closest_feature_id)
            attributes_text = "\n".join(
                [f"{field.name()}: {value}" for field, value in zip(layer.fields(), closest_feature.attributes())]
            )
            point = closest_feature.geometry().asPoint()
            if point:
                x, y = point.x(), point.y()
                coordinates_text = f"Coordinates: ({x:.5f}, {y:.5f})\n"
            self.ui.te_info.setPlainText(f"Selected feature:\n{coordinates_text+attributes_text}")
            if not ref:
                self.highlightSelectedFeatures(closest_feature.geometry())
            else:
                self.highlightSelectedReferenceFeature(closest_feature.geometry())

        return closest_feature

    def highlightSelectedFeatures(self, geometry: QgsGeometry, layer: QgsMapLayer = None) -> None:
        """
        Highlight the selected feature
        :param geometry: QgsGeometry
        :param layer: QgsMapLayer
        """
        if not layer:
            layer = self.iface.activeLayer()
        self.clearFeatureHighlight()
        self.highlight = QgsHighlight(self.iface.mapCanvas(), geometry, layer)
        self.highlight.setColor(Qt.yellow)
        self.highlight.show()

    def highlightSelectedReferenceFeature(self, geometry: QgsGeometry, layer: QgsMapLayer = None) -> None:
        if not layer:
            layer = self.iface.activeLayer()
        self.clearReferenceFeatureHighlight()
        self.reference_highlight = QgsHighlight(self.iface.mapCanvas(), geometry, layer)
        self.reference_highlight.setColor(Qt.red)
        self.reference_highlight.show()

    def clearFeatureHighlight(self) -> None:
        if self.highlight:
            self.highlight.hide()
            self.highlight = None

    def clearReferenceFeatureHighlight(self) -> None:
        """
        Clear reference feature highlight
        """
        if self.reference_highlight:
            self.reference_highlight.hide()
            self.reference_highlight = None

    @classmethod
    def findFeatureAtPoint(cls, layer, point, canvas, only_the_closest_one=True, only_ids=False):
        """
        Find the closest feature to the clicked point
        :param layer: QgsMapLayer
        :param point: QgsPointXY
        :param canvas: QgsMapCanvas
        :param only_the_closest_one: bool
        :param only_ids: bool
        :return: closest feature or feature ID
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        settings = QgsSettings()
        radius = settings.value("/Map/searchRadiusMM", Qgis.DEFAULT_SEARCH_RADIUS_MM, type=float)
        if radius <= 0:
            radius = Qgis.DEFAULT_SEARCH_RADIUS_MM
        radius = canvas.extent().width() * radius / canvas.size().width()
        radius *= 5
        rect = QgsRectangle(point.x() - radius, point.y() - radius, point.x() + radius, point.y() + radius)
        rect = canvas.mapSettings().mapToLayerCoordinates(layer, rect)
        point_map = canvas.mapSettings().mapToLayerCoordinates(layer, point)
        ret = None

        if only_the_closest_one:
            request = QgsFeatureRequest()
            request.setFilterRect(rect)
            min_dist = -1
            feature_id = None
            for f in layer.getFeatures(request):
                geom = f.geometry()
                distance = geom.distance(QgsGeometry.fromPointXY(point_map))
                if min_dist < 0 or distance < min_dist:
                    min_dist = distance
                    feature_id = f.id()
            if only_ids:
                ret = feature_id
            elif feature_id is not None:
                ret = layer.getFeature(feature_id)
        else:
            ids = [f.id() for f in layer.getFeatures()]
            if only_ids:
                ret = ids
            else:
                ret = []
                request = QgsFeatureRequest()
                request.setFilterFids(ids)
                for f in layer.getFeatures(request):
                    ret.append(f)

        QApplication.restoreOverrideCursor()
        return ret

class TSClickHandler(MapClickHandler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.plot_ts = pts.PlotTs(self.ui)
        self.ts_values = 0
        self.ref_values = 0

    def choosePointClicked(self, *, point: QgsPointXY, layer: QgsMapLayer = None, ref=False):
        if not layer:
            layer = self.iface.activeLayer()
        status_vector, message = vector_layer_utils.checkVectorLayer(layer)
        status_raster, message = gmtsar_layer_utils.checkGmtsarLayer(layer)
        if status_vector:
            self.choosePointClickedVector(point=point, layer=layer, ref=ref)
        elif status_raster:
            self.choosePointClickedRaster(point=point, layer=layer, ref=ref)
        else:
            return


    def choosePointClickedVector(self, *, point: QgsPointXY, layer: QgsMapLayer = None, ref=False):
        feature = self.identifyClickedFeature(point, layer=layer, ref=ref)

        status, message = vector_layer_utils.checkVectorLayerTimeseries(layer)
        if status is False:
            self.ui.lb_msg_bar.setText(message)
            return

        if feature:
            attributes = getFeatureAttributes(feature)
            date_values = extractDateValueAttributes(attributes)
            if not ref:
                self.ts_values = date_values[:, 1]
            else:
                self.ref_values = date_values[:, 1]

            dates = date_values[:, 0]
            self.plot_ts.plotTs(dates=dates, ts_values=self.ts_values, ref_values=self.ref_values)

    def choosePointClickedRaster(self, *, point: QgsPointXY, layer: QgsMapLayer = None, ref=False):
        status, message = gmtsar_layer_utils.checkGmtsarLayerTimeseries(layer)
        if status is False:
            self.ui.lb_msg_bar.setText(message)
            return

        date_values = getGmtsarTimeseriesAttributes(layer, point=point)

        if date_values.size == 0:
            return

        clicked_point = QgsGeometry.fromPointXY(point)
        if not ref:
            self.highlightSelectedFeatures(clicked_point)
        else:
            self.highlightSelectedReferenceFeature(clicked_point)

        if not ref:
            self.ts_values = date_values[:, 1]
        else:
            self.ref_values = date_values[:, 1]

        dates = date_values[:, 0]
        self.plot_ts.plotTs(dates=dates, ts_values=self.ts_values, ref_values=self.ref_values)

    def resetReferencePoint(self):
        self.ref_values = 0
        self.clearReferenceFeatureHighlight()
        self.plot_ts.plotTs(ref_values=self.ref_values)


def getGmtsarTimeseriesAttributes(layer, point: QgsPointXY) -> dict:
    """
    Get the timeseries values of the clicked point from the GMTSAR grd files.
    The grd files should be in the same directory as the layer (typically velocity) file.
    """
    file_path = layer.source()
    directory = os.path.dirname(file_path)
    pattern = re.compile(r'^\d{8}_.*\.grd')

    grd_files = [f for f in os.listdir(directory) if pattern.match(f)]

    if not grd_files:
        return np.array([])

    date_value_list = []
    first_grd_file_full_path = os.path.join(directory, grd_files[0])
    dataset = gdal.Open(first_grd_file_full_path)
    if not dataset:
        return np.array([])

    transform = dataset.GetGeoTransform()
    inv_transform = gdal.InvGeoTransform(transform)

    x, y = point.x(), point.y()
    px, py = gdal.ApplyGeoTransform(inv_transform, x, y)

    grd_file_paths = [os.path.join(directory, grd_file) for grd_file in grd_files]
    date_objs = [datetime.strptime(grd_file[:8], '%Y%m%d') for grd_file in grd_files]

    for grd_file_full_path, date_obj in zip(grd_file_paths, date_objs):
        dataset = gdal.Open(grd_file_full_path)

        if not dataset:
            continue

        band = dataset.GetRasterBand(1)
        x_size = band.XSize
        y_size = band.YSize
        if not (0 <= px < x_size and 0 <= py < y_size):
            return np.array([])

        pixel_value = band.ReadAsArray(int(px), int(py), 1, 1)[0, 0]

        # if not pixel_value == band.GetNoDataValue():
        #     date_value_list.append((date_obj, pixel_value))
        if not np.isnan(pixel_value):
            date_value_list.append((date_obj, pixel_value))

    return np.array(date_value_list, dtype=object)


def getFeatureAttributes(feature: QgsFeature) -> dict:
    """
    Get the attributes of a feature as a dictionary.
    :param feature: QgsFeature
    :return: Dictionary of feature attributes
    """
    return {field.name(): feature[field.name()] for field in feature.fields()}



def extractDateValueAttributes(attributes: dict) -> list:
    """
    Extract attributes with keys in the format 'DYYYYMMDD' and return a list of tuples with datetime and float value.
    :param attributes: Dictionary of feature attributes
    :return: List of tuples (datetime, float)
    """
    date_value_pattern = re.compile(r'^D(\d{8})$')
    date_value_list = []

    for key, value in attributes.items():
        match = date_value_pattern.match(key)
        if match:
            date_str = match.group(1)
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            date_value_list.append((date_obj, float(value)))

    return np.array(date_value_list, dtype=object)
from qgis.PyQt.QtWidgets import QMessageBox, QApplication
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsPointXY, QgsGeometry, QgsMapLayer, QgsRectangle, QgsFeatureRequest, QgsSettings, Qgis
from qgis.gui import QgsHighlight
from PyQt5.QtGui import QCursor


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

    def identifyClickedFeatureID(self, point: QgsPointXY, layer: QgsMapLayer = None) -> int:
        """
        Identify the closest feature to the clicked point
        :param point: QgsPointXY
        :param layer: QgsMapLayer
        :return: closest feature ID
        """
        if not layer:
            layer = self.iface.activeLayer()

        if not (layer and layer.isValid()):
            self.ui.label_message.setText("Invalid Layer: Please select a valid layer.")
            return
        elif not (layer.type() == QgsMapLayer.VectorLayer):
            self.ui.label_message.setText("Only vector layers supported: Please select a valid vector layer.")
            return
        elif not (layer.geometryType() == 0):
            self.ui.label_message.setText("Invalid Layer: Please select a valid point layer.")
            return

        closest_feature_id = self.findFeatureAtPoint(layer, point, self.iface.mapCanvas(),
                                                     only_the_closest_one=True, only_ids=True)

        if closest_feature_id:
            self.ui.label_message.setText(f"Identify Result: Closest feature ID is {closest_feature_id}")
        else:
            self.ui.label_message.setText("Identify Result: No nearby point found.")

        return closest_feature_id

    def identifyClickedFeature(self, point: QgsPointXY, layer: QgsMapLayer = None) -> QgsGeometry:
        """
        Identify the closest feature to the clicked point and display its attributes
        :param point: QgsPointXY
        :param layer: QgsMapLayer
        :return: closest feature
        """
        if not layer:
            layer = self.iface.activeLayer()
        closest_feature_id = self.identifyClickedFeatureID(point, layer)

        closest_feature = None
        if closest_feature_id:
            closest_feature = layer.getFeature(closest_feature_id)
            attributes_text = "\n".join(
                [f"{field.name()}: {value}" for field, value in zip(layer.fields(), closest_feature.attributes())]
            )
            self.ui.label_message.setText(f"Identify Result: Closest feature attributes:\n{attributes_text}")
            self.highlightSelectedFeatures(closest_feature.geometry())

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

    def clearFeatureHighlight(self) -> None:
        if self.highlight:
            self.highlight.hide()
            self.highlight = None

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
        radius = canvas.extent().width() * radius / 100
        rect = QgsRectangle(point.x() - radius, point.y() - radius, point.x() + radius, point.y() + radius)
        rect = canvas.mapSettings().mapToLayerCoordinates(layer, rect)
        ret = None

        if only_the_closest_one:
            request = QgsFeatureRequest()
            request.setFilterRect(rect)
            min_dist = -1
            feature_id = None
            rect = QgsGeometry.fromRect(rect)
            for f in layer.getFeatures(request):
                geom = f.geometry()
                distance = geom.distance(rect)
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
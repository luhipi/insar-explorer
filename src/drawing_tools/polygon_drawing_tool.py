from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsGeometry, QgsWkbTypes
from qgis.PyQt.QtGui import QColor as QgsColor


class PolygonMarker(QgsMapTool):
    def __init__(self, canvas) -> None:
        super().__init__(canvas)
        self.canvas = canvas
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.points = []

        self.setStyle()

    def setStyle(self, color=(150, 150, 50, 80), stroke_color=(250, 250, 250, 100), stroke_width=2) -> None:
        """Set the fill and edge color of the polygon"""
        self.rubber_band.setFillColor(QgsColor(*color))
        self.rubber_band.setStrokeColor(QgsColor(*stroke_color))
        self.rubber_band.setWidth(stroke_width)

    def addPoint(self, point):
        self.points.append(point)
        self.rubber_band.addPoint(point, True)

    def reset(self):
        self.points = []
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)

    def stopDrawing(self):
        self.points = []


class PolygonDrawingTool(QgsMapTool):
    def __init__(self, canvas, callback=None, start_callback=None) -> None:
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback  # Function to call when polygon is complete
        self.start_callback = start_callback  # Function to call before starting the drawing
        self.polygon_marker = PolygonMarker(self.canvas)
        self.first_point = True
        self.last_point = False

    def canvasPressEvent(self, event) -> None:
        """Add the clicked point to the polygon"""
        if event.button() == 1:  # Left-click
            if self.first_point:
                self.activate()
                if self.start_callback:
                    self.start_callback()
                self.first_point = False
            if self.last_point:
                self.cancelDrawing()
                self.last_point = False

            # Add the clicked point to the polygon
            point = self.toMapCoordinates(event.pos())
            self.polygon_marker.addPoint(point)

    def canvasReleaseEvent(self, event) -> None:
        """Check for right-click to finalize the polygon"""
        if event.button() == 2:  # Right-click
            if len(self.polygon_marker.points) > 2:  # A valid polygon requires at least 3 points
                self.finalizePolygon()
                self.last_point = True
                self.first_point = True
            else:
                self.cancelDrawing()
                self.first_point = True

    def finalizePolygon(self) -> None:
        """Create a polygon geometry"""
        if len(self.polygon_marker.points) > 2:
            polygon = QgsGeometry.fromPolygonXY([self.polygon_marker.points])
            if self.callback:
                self.callback(polygon)
        # self.clear()

    def cancelDrawing(self) -> None:
        """Clear the drawing"""
        # self.clear()
        self.polygon_marker.stopDrawing()

    def clear(self) -> None:
        """Reset points and rubber band"""
        # self.polygon_marker.points = []
        # self.polygon_marker.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.polygon_marker.reset()
        self.deactivate()

    def activate(self):
        self.polygon_marker.reset()
        # super().activate()

    def deactivate(self) -> None:
        """Clear the drawing and deactivate the tool"""
        super().deactivate()
        # self.clear()

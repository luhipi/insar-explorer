from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsGeometry, QgsWkbTypes
from qgis.PyQt.QtGui import QColor as QgsColor


class PolygonDrawingTool(QgsMapTool):
    def __init__(self, canvas, callback=None) -> None:
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback  # Function to call when polygon is complete
        self.points = []  # List to store points of the polygon
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)  # Rubber band for drawing
        self.setStyle()

        self.last_point = False

    def canvasPressEvent(self, event) -> None:
        """Add the clicked point to the polygon"""
        if event.button() == 1:  # Left-click
            if self.last_point:
                self.cancelDrawing()
                self.last_point = False

        # Add the clicked point to the polygon
        point = self.toMapCoordinates(event.pos())
        self.points.append(point)
        self.rubber_band.addPoint(point, True)

    def canvasReleaseEvent(self, event) -> None:
        """Check for right-click to finalize the polygon"""
        if event.button() == 2:  # Right-click
            if len(self.points) > 2:  # A valid polygon requires at least 3 points
                self.finalizePolygon()
                self.last_point = True
            else:
                self.cancelDrawing()

    def finalizePolygon(self) -> None:
        """Create a polygon geometry"""
        if len(self.points) > 2:
            polygon = QgsGeometry.fromPolygonXY([self.points])
            if self.callback:
                self.callback(polygon)
        # self.clear()

    def cancelDrawing(self) -> None:
        """Clear the drawing"""
        self.clear()

    def clear(self) -> None:
        """Reset points and rubber band"""
        self.points = []
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)

    def deactivate(self) -> None:
        """Clear the drawing and deactivate the tool"""
        super().deactivate()
        self.clear()

    def setStyle(self, color=(100, 100, 100, 80), stroke_color=(250, 250, 250, 100), stroke_width=2) -> None:
        """Set the fill and edge color of the polygon"""
        self.rubber_band.setFillColor(QgsColor(*color))
        self.rubber_band.setStrokeColor(QgsColor(*stroke_color))
        self.rubber_band.setWidth(stroke_width)
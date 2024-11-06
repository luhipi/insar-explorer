from qgis.PyQt.QtGui import QColor


class ColorMaps():
    def __init__(self):
        self.ramp = []

    def getColor(self, value):
        color_stops = self.ramp
        for i in range(len(color_stops) - 1):
            pos1, color1 = color_stops[i]
            pos2, color2 = color_stops[i + 1]

            if pos1 <= value <= pos2:
                ratio = (value - pos1) / (pos2 - pos1)
                r = color1.red() + (color2.red() - color1.red()) * ratio
                g = color1.green() + (color2.green() - color1.green()) * ratio
                b = color1.blue() + (color2.blue() - color1.blue()) * ratio
                return QColor(int(r), int(g), int(b))

        return color_stops[-1][1]


class turbo(ColorMaps):
    def __init__(self):
        super().__init__()
        self.ramp = [
                (0.0, QColor(66, 30, 150)),  # Dark blue
                (0.1, QColor(29, 81, 201)),  # Darker blue
                (0.2, QColor(25, 150, 221)),  # Blue
                (0.3, QColor(18, 201, 187)),  # Cyan
                (0.4, QColor(33, 233, 127)),  # Greenish-cyan
                (0.5, QColor(93, 242, 73)),  # Green
                (0.6, QColor(170, 250, 42)),  # Yellow-green
                (0.7, QColor(239, 234, 26)),  # Yellow
                (0.8, QColor(252, 186, 28)),  # Yellow-orange
                (0.9, QColor(252, 102, 28)),  # Orange-red
                (1.0, QColor(252, 53, 28))  # Red
            ]

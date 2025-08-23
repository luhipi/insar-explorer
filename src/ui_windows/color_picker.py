from PyQt5.QtWidgets import QColorDialog
from qgis.PyQt.QtGui import QColor


class ColorPicker:
    def __init__(self, initial_color, use_native_flag=False, parent=None):
        self.parent = parent
        self.color = initial_color
        self.use_native_flag = use_native_flag

        self.color_dialog = QColorDialog()
        self.custom_colors = [
            "#1f77b4",  # Blue
            "#ff7f0e",  # Orange
            "#2ca02c",  # Green
            "#d62728",  # Red
            "#9467bd",  # Purple
            "#8c564b",  # Brown
            "#e377c2",  # Pink
            "#7f7f7f",  # Gray
            "#bcbd22",  # Yellow-green
            "#17becf"  # Cyan
        ]
        for i in range(10):  # QColorDialog supports up to 16 custom colors
            self.color_dialog.setCustomColor(i, QColor(255, 255, 255))

        for i, custom_color in enumerate(self.custom_colors):
            self.color_dialog.setCustomColor(i, QColor(custom_color))

    def setCustomColors(self, custom_colors=None):
        #  Hint: Mac Native Dialog does not setCustomColor
        if custom_colors is not None:
            self.custom_colors = custom_colors

        # clear the firt 10 custom colors if there is a new list
        # leave the last 6 custom colors unchanged, for more flexibility
        for i in range(10):  # QColorDialog supports up to 16 custom colors
            self.color_dialog.setCustomColor(i, QColor(255, 255, 255))

        for i, custom_color in enumerate(self.custom_colors):
            self.color_dialog.setCustomColor(i, QColor(custom_color))

    def openColorDialog(self):
        """ Opens a color dialog to select a new color. """
        initial_color = QColor(self.color)
        color_dialog = self.color_dialog

        self.setCustomColors()

        if self.use_native_flag:
            color = color_dialog.getColor(initial_color)
        else:
            color = color_dialog.getColor(initial_color, options=QColorDialog.DontUseNativeDialog)

        if color.isValid():
            self.color = color.name()

    def getColor(self):
        return self.color

    def pickColor(self):
        """ Opens the color dialog and returns the selected color. """
        self.openColorDialog()
        return self.getColor()

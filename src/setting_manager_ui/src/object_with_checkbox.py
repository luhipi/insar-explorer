try:
    from PySide6.QtWidgets import (
        QWidget,
        QPushButton,
        QHBoxLayout,
        QColorDialog,
        QCheckBox,
        QSpinBox,
        QDoubleSpinBox,
        QSizePolicy,
        QLineEdit,
        QComboBox
    )
    from PySide6.QtGui import QColor
except ImportError:
    from qgis.PyQt.QtWidgets import (
        QWidget,
        QPushButton,
        QHBoxLayout,
        QColorDialog,
        QCheckBox,
        QSpinBox,
        QDoubleSpinBox,
        QSizePolicy,
        QLineEdit,
        QComboBox
    )
    from qgis.PyQt.QtGui import QColor


class ColorPicker(QWidget):
    """
    A widget for selecting colors.

    :param initial_color: The initial color to be set.
    :type initial_color: str
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """
    def __init__(self, initial_color, use_native_flag=False, parent=None):
        super().__init__(parent)
        self.color = initial_color
        self.layout = QHBoxLayout(self)
        self.button = QPushButton()
        self.button.setStyleSheet(f"background-color: {self.color}")
        self.button.clicked.connect(self.openColorDialog)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

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

    def setCustomColors(self, custom_colors=[]):
        """
        Sets the custom colors for the color dialog.

        :param custom_colors: The list of custom colors.
        :type custom_colors: list of str
        """
        #  Hint: Mac Native Dialog does not setCustomColor
        if len(custom_colors) > 0:
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
            self.button.setStyleSheet(f"background-color: {self.color}")

    def getColor(self):
        """
        Gets the current color.

        :return: The current color.
        :rtype: str
        """
        return self.color

    def setColor(self, color):
        """
        Sets a new color.

        :param color: The new color to be set.
        :type color: str
        """
        self.color = color
        self.button.setStyleSheet(f"background-color: {self.color}")


class ObjectWithCheckbox(QWidget):
    """
    A base widget that includes a main widget and an optional checkbox.

    :param value: The initial value of the main widget.
    :type value: any
    :param flag: A flag indicating the initial state of the main widget.
    :type flag: bool
    :param checkbox: Whether to include a checkbox.
    :type checkbox: bool, optional
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """

    def __init__(self, value, flag, checkbox=False, parent=None):
        super().__init__(parent)
        self.value = value
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Set layout margins to zero
        self.wobject = None
        self.addObject()
        if checkbox:
            self.checkbox = QCheckBox()
            self.checkbox.setChecked(not flag)
            self.checkbox.stateChanged.connect(self.toggleObject)
            self.layout.addWidget(self.checkbox)
            self.layout.addWidget(self.checkbox)
            self.checkbox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        else:
            self.checkbox = None

        self.layout.addWidget(self.wobject)
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Adjust size policy
        self.wobject.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setEnabled(flag)

    def addObject(self):
        """ Adds the main widget. This method should be overridden by subclasses. """
        pass

    def setEnabled(self, flag):
        self.wobject.setEnabled(not flag)

    def toggleObject(self, state):
        """
        Toggles the enabled state of the main widget.

        :param state: The state of the checkbox.
        :type state: int
        """

        self.wobject.setEnabled(state)

    def isAuto(self):
        """
        Checks if the checkbox is in the auto state.

        :return: True if the checkbox is in the auto state, False otherwise.
        :rtype: bool
        """

        if self.checkbox:
            return not self.checkbox.isChecked()
        else:
            return False


class LineEditWithCheckbox(ObjectWithCheckbox):
    """
    A widget that includes a QLineEdit and an optional checkbox.

    :param value: The initial text of the QLineEdit.
    :type value: str
    :param flag: A flag indicating the initial state of the QLineEdit.
    :type flag: bool
    :param checkbox: Whether to include a checkbox.
    :type checkbox: bool, optional
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """
    def __init__(self, value, flag, checkbox=False, parent=None):
        super().__init__(value, flag, checkbox, parent)

    def addObject(self):
        """ Adds a QLineEdit as the main widget. """
        self.wobject = QLineEdit()
        self.wobject.setText(self.value)

    def setValue(self, value):
        """
        Sets the text of the QLineEdit.

        :param value: The new text to be set.
        :type value: str
        """
        self.wobject.setText(value)

    def getValue(self):
        """
        Gets the text of the QLineEdit.

        :return: The current text.
        :rtype: str
        """
        return self.wobject.text()


class SpinBoxWithCheckbox(ObjectWithCheckbox):
    """
    A widget that includes a QSpinBox and an optional checkbox.

    :param value: The initial value of the QSpinBox.
    :type value: int
    :param flag: A flag indicating the initial state of the QSpinBox.
    :type flag: bool
    :param checkbox: Whether to include a checkbox.
    :type checkbox: bool, optional
    :param range: The range of the QSpinBox, defaults to [None, None].
    :type range: list of int, optional
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """
    def __init__(self, value, flag, checkbox=False, range=[None, None], parent=None):
        self.range = range
        super().__init__(value, flag, checkbox, parent)

    def addObject(self):
        """ Adds a QSpinBox as the main widget. """
        self.wobject = QSpinBox()
        if self.range[0] is not None:
            self.wobject.setMinimum(self.range[0])
        if self.range[1] is not None:
            self.wobject.setMaximum(self.range[1])

    def setValue(self, value):
        """
        Sets the value of the QSpinBox.

        :param value: The new value to be set.
        :type value: int
        """
        self.wobject.setValue(value)

    def getValue(self):
        """
        Gets the value of the QSpinBox.

        :return: The current value.
        :rtype: int
        """
        return self.wobject.value()


class DoubleSpinBoxWithCheckbox(ObjectWithCheckbox):
    """
    A widget that includes a QDoubleSpinBox and an optional checkbox.

    :param value: The initial value of the QDoubleSpinBox.
    :type value: float
    :param flag: A flag indicating the initial state of the QDoubleSpinBox.
    :type flag: bool
    :param checkbox: Whether to include a checkbox.
    :type checkbox: bool, optional
    :param range: The range of the QDoubleSpinBox, defaults to [None, None].
    :type range: list of float, optional
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """
    def __init__(self, value, flag, checkbox=False, range=[None, None], parent=None):
        self.range = range
        super().__init__(value, flag, checkbox, parent)

    def addObject(self):
        """ Adds a QDoubleSpinBox as the main widget. """
        self.wobject = QDoubleSpinBox()
        if self.range[0] is not None:
            self.wobject.setMinimum(float(self.range[0]))
        if self.range[1] is not None:
            self.wobject.setMaximum(float(self.range[1]))

    def setValue(self, value):
        """
        Sets the value of the QDoubleSpinBox.

        :param value: The new value to be set.
        :type value: float
        """
        self.wobject.setValue(value)

    def getValue(self):
        """
        Gets the value of the QDoubleSpinBox.

        :return: The current value.
        :rtype: float
        """
        return self.wobject.value()


class ComboBoxWithCheckbox(ObjectWithCheckbox):
    """
    A widget that includes a QComboBox and an optional checkbox.

    :param value: The initial value of the QComboBox.
    :type value: str
    :param flag: A flag indicating the initial state of the QComboBox.
    :type flag: bool
    :param checkbox: Whether to include a checkbox.
    :type checkbox: bool, optional
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """
    def __init__(self, value, flag, checkbox=False, options=[], parent=None):
        super().__init__(value, flag, checkbox, parent)
        if len(options) > 0:
            self.addItems(options)
            self.setCurrentText(value)

    def addItems(self, items):
        """
        Adds items to the QComboBox.

        :param items: The items to be added.
        :type items: list of str
        """
        self.wobject.addItems(items)

    def setCurrentText(self, text):
        """
        Sets the current text of the QComboBox.

        :param text: The text to be set.
        :type text: str
        """
        self.wobject.setCurrentText(text)

    def addObject(self):
        """ Adds a QComboBox as the main widget. """
        self.wobject = QComboBox()

    def setValue(self, value):
        """
        Sets the current text of the QComboBox.

        :param value: The text to be set.
        :type value: str
        """
        self.wobject.setCurrentText(value)

    def getValue(self):
        """
        Gets the current text of the QComboBox.

        :return: The current text.
        :rtype: str
        """
        return self.wobject.currentText()


class ColorPickerWithCheckbox(ObjectWithCheckbox):
    """
    A widget that includes a ColorPicker and an optional checkbox.

    :param value: The initial color of the ColorPicker.
    :type value: str
    :param flag: A flag indicating the initial state of the ColorPicker.
    :type flag: bool
    :param checkbox: Whether to include a checkbox.
    :type checkbox: bool, optional
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """
    def __init__(self, value, flag, checkbox=False, options=[], parent=None):
        super().__init__(value, flag, checkbox, parent)
        self.options = options
        self.setCustomColors()

    def setCustomColors(self, options=[]):
        if len(options) == 0:
            options = self.options
        self.wobject.setCustomColors(options)

    def addObject(self):
        """ Adds a ColorPicker as the main widget. """
        self.wobject = ColorPicker(self.value)

    def setValue(self, value):
        """
        Sets the color of the ColorPicker.

        :param value: The new color to be set.
        :type value: str
        """
        self.wobject.setColor(value)

    def getValue(self):
        """
        Gets the color of the ColorPicker.

        :return: The current color.
        :rtype: str
        """
        return self.wobject.getColor()

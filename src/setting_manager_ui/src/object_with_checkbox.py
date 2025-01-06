try:
    from PySide6.QtWidgets import (
        QWidget,
        QPushButton,
        QHBoxLayout,
        QMessageBox,
        QColorDialog,
        QCheckBox,
        QSpinBox,
        QDoubleSpinBox,
        QSizePolicy,
        QLineEdit,
        QComboBox
    )
except ImportError:
    from qgis.PyQt.QtWidgets import (
        QWidget,
        QPushButton,
        QHBoxLayout,
        QMessageBox,
        QColorDialog,
        QCheckBox,
        QSpinBox,
        QDoubleSpinBox,
        QSizePolicy,
        QLineEdit,
        QComboBox
    )


class ColorPicker(QWidget):
    """
    A widget for selecting colors.

    :param initial_color: The initial color to be set.
    :type initial_color: str
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """
    def __init__(self, initial_color, parent=None):
        super().__init__(parent)
        self.color = initial_color
        self.layout = QHBoxLayout(self)
        self.button = QPushButton()
        self.button.setStyleSheet(f"background-color: {self.color}")
        self.button.clicked.connect(self.openColorDialog)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

    def openColorDialog(self):
        """ Opens a color dialog to select a new color. """
        color = QColorDialog.getColor()
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
        self.addObject(flag)
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

    def addObject(self, flag):
        """ Adds the main widget. This method should be overridden by subclasses. """
        pass

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

    def addObject(self, flag):
        """ Adds a QLineEdit as the main widget. """
        self.wobject = QLineEdit()
        self.wobject.setText(self.value)
        self.wobject.setEnabled(not flag)

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

    def addObject(self, flag):
        """ Adds a QSpinBox as the main widget. """
        self.wobject = QSpinBox()
        self.wobject.setEnabled(not flag)
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

    def addObject(self, flag):
        """ Adds a QDoubleSpinBox as the main widget. """
        self.wobject = QDoubleSpinBox()
        self.wobject.setEnabled(not flag)
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
    def __init__(self, value, flag, checkbox=False, parent=None):
        super().__init__(value, flag, checkbox, parent)

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

    def addObject(self, flag):
        """ Adds a QComboBox as the main widget. """
        self.wobject = QComboBox()
        self.wobject.setEnabled(not flag)

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
    def __init__(self, value, flag, checkbox=False, parent=None):
        super().__init__(value, flag, checkbox, parent)

    def addObject(self, flag):
        """ Adds a ColorPicker as the main widget. """
        self.wobject = ColorPicker(self.value)
        self.wobject.setEnabled(not flag)

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



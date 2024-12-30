__version__ = '0.1.0'

import sys

try:
    # pyside6
    from PySide6.QtWidgets import (
        QApplication,
        QDialog,
        QVBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QColor, QBrush
except ImportError:
    # QGIS
    from qgis.PyQt.QtWidgets import (
        QApplication,
        QDialog,
        QVBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
    )
    from qgis.PyQt.QtCore import Qt, pyqtSignal as Signal
    from qgis.PyQt.QtGui import QColor, QBrush

from json_settings import JsonSettings
from src.object_with_checkbox import *


class SettingsTabWidget(QTableWidget):
    """
    A table widget for displaying and editing settings parameters.

    :param section_name: The name of the settings section.
    :type section_name: str
    :param params_dict: A dictionary of parameters and their properties.
    :type params_dict: dict
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """

    def __init__(self, section_name, params_dict, parent=None):
        super().__init__(parent)
        self.section_name = section_name
        self.params_dict = params_dict

        self.param_types = {}
        self.param_types_defaults = {}

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Parameter", "Value", "Default"])

        self.verticalHeader().setVisible(False)

        self.loadData()

    def loadData(self):
        """ Loads the parameters into the table widget. """

        # TODO: implement a way to hide/show certain parameters
        param_dict_visible = self.params_dict

        self.setRowCount(len(param_dict_visible))

        for row_idx, (param_name, info) in enumerate(param_dict_visible.items()):
            param_type = info.get("type", "string")
            param_value = info.get("value", "")
            param_default = info.get("default", "")
            auto_flag = info.get("auto", False)
            options = info.get("options", None)

            # add auto checkbox if auto flag is present
            add_checkbox = "auto" in info

            # store type and default in a dictionary for later use
            self.param_types_defaults[param_name] = (param_type, param_default, auto_flag)

            # Column 0: Parameter name (read-only)
            param_item = QTableWidgetItem(param_name)
            param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row_idx, 0, param_item)
            param_item.setBackground(QBrush(QColor(240, 240, 240)))  # Light gray background

            # Column 1: Value (editable)
            if param_type == "color":
                wobject = ColorPickerWithCheckbox(param_value, auto_flag, add_checkbox)
            elif param_type == "bool":
                wobject = QCheckBox()
                wobject.setChecked(param_value)
            elif param_type == "float":
                wobject = DoubleSpinBoxWithCheckbox(param_value, auto_flag, add_checkbox)
                wobject.setValue(param_value)

            elif param_type == "int":
                wobject = SpinBoxWithCheckbox(param_value, auto_flag, add_checkbox)
                wobject.setValue(param_value)

            elif param_type == "string":
                wobject = LineEditWithCheckbox(param_value, auto_flag, add_checkbox)
                wobject.setValue(param_value)

            elif param_type == "dropdown":
                wobject = ComboBoxWithCheckbox(param_value, auto_flag, add_checkbox)
                wobject.addItems(options)
                wobject.setCurrentText(param_value)
            else:
                QMessageBox.warning(self, "Unknown parameter type", f"Unknown parameter type: {param_type}")
                raise ValueError(f"Unknown parameter type: {param_type}")

            self.setCellWidget(row_idx, 1, wobject)

            # Column 2: Default value (read-only)
            default_item = QTableWidgetItem(str(param_default))
            default_item.setFlags(default_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row_idx, 2, default_item)
            default_item.setBackground(QBrush(QColor(250, 255, 250)))


class SettingsTableDialog(QDialog):
    """
    A dialog for displaying and editing settings in a tabbed interface.

    :param json_file: The path to the JSON file containing the settings.
    :type json_file: str
    :param block_key: The key for a specific block of settings, defaults to None.
    :type block_key: str, optional
    :param parent: The parent widget.
    :type parent: QWidget, optional
    """

    # signal emitted when the apply button is clicked
    applyClicked = Signal()

    def __init__(self, json_file, block_key=None, parent=None):
        super().__init__(parent)
        self.json_file = json_file
        self.block_key = block_key
        self.settings_dict = {}

        self.settings = JsonSettings(self.json_file)
        self.setWindowTitle("Settings")

        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        # OK button
        self.save_button = QPushButton("Ok")
        self.save_button.clicked.connect(self.onOkClicked)
        button_layout.addWidget(self.save_button)

        # Apply button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.onApplyClicked)
        button_layout.addWidget(self.apply_button)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(lambda: self.resetToDefault(reset_all=False))
        button_layout.addWidget(self.reset_button)

        # Reset All button
        self.reset_all_button = QPushButton("Reset All")
        self.reset_all_button.clicked.connect(lambda: self.resetToDefault(reset_all=True))
        button_layout.addWidget(self.reset_all_button)

        # Cancel button
        self.close_button = QPushButton("Cancel")
        self.close_button.clicked.connect(self.reject)
        button_layout.addWidget(self.close_button)

        self.loadData()

    def loadData(self):
        """ Reads the entire JSON file and extracts only the block we care about. """
        settings_block = self.settings.load(self.block_key)

        for section_name, params_dict in settings_block.items():
            table = SettingsTabWidget(section_name, params_dict, parent=self.tab_widget)
            self.tab_widget.addTab(table, section_name)

    def collectData(self):
        """
        Collects data from all tabs and updates the JSON block.

        :return: The updated settings block.
        :rtype: dict
        """
        # read JSON
        settings_block = self.settings.load(self.block_key)

        # collect data from each tab
        try:
            for i in range(self.tab_widget.count()):
                table_widget = self.tab_widget.widget(i)  # a SettingsTabWidget
                section_name = table_widget.section_name

                # Update the specific part of the JSON file
                if section_name in settings_block:
                    for row_index in range(table_widget.rowCount()):
                        param_name_item = table_widget.item(row_index, 0)
                        if param_name_item:
                            param_name = param_name_item.text()
                            if param_name in settings_block[section_name]:
                                widget = table_widget.cellWidget(row_index, 1)
                                if widget:
                                    if isinstance(widget, QCheckBox):
                                        settings_block[section_name][param_name]['value'] = widget.isChecked()
                                    else:
                                        settings_block[section_name][param_name]['value'] = widget.getValue()

                                    if 'auto' in settings_block[section_name][param_name]:
                                        settings_block[section_name][param_name]['auto'] = widget.isAuto()

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
            return

        return settings_block

    def resetToDefault(self, reset_all=False):
        """
        Resets the settings to their default values.

        :param reset_all: Whether to reset all settings or only the selected ones.
        :type reset_all: bool
        """

        if reset_all:
            for i in range(self.tab_widget.count()):
                table_widget = self.tab_widget.widget(i)  # Get each SettingsTabWidget
                self.resetTableWidgetToDefault(table_widget)
        else:
            table_widget = self.tab_widget.currentWidget()  # Get the current SettingsTabWidget
            selected_ranges = table_widget.selectedRanges()  # Get selected ranges from the table widget
            for selected_range in selected_ranges:
                for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                    self.resetRowToDefault(table_widget, row)

    def resetTableWidgetToDefault(self, table_widget):
        """
        Resets all rows in the given table widget to their default values.

        :param table_widget: The table widget to reset.
        :type table_widget: SettingsTabWidget
        """
        for row in range(table_widget.rowCount()):
            self.resetRowToDefault(table_widget, row)

    def resetRowToDefault(self, table_widget, row):
        """
        Resets a specific row in the given table widget to its default value.

        :param table_widget: The table widget containing the row.
        :type table_widget: SettingsTabWidget
        :param row: The row index to reset.
        :type row: int
        """
        param_name_item = table_widget.item(row, 0)
        if param_name_item:
            param_name = param_name_item.text()
            if param_name in table_widget.param_types_defaults:
                param_type, param_default, auto_flag = table_widget.param_types_defaults[param_name]
                widget = table_widget.cellWidget(row, 1)
                if widget:
                    if isinstance(widget, QCheckBox):
                        widget.setChecked(param_default)
                    else:
                        if widget.checkbox:
                            widget.checkbox.setChecked(not auto_flag)
                        else:
                            widget.setValue(param_default)

    def onOkClicked(self):
        """ Handles the OK button click event. """
        self.saveData()
        self.accept()

    def onApplyClicked(self):
        """ Handles the Apply button click event. """
        self.saveData()
        self.applyClicked.emit()

    def saveData(self):
        """ Saves the collected data to the JSON file. """
        settings_block = self.collectData()
        self.settings.save(self.block_key, settings_block)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    JSON_FILE = "../tests/test.json"
    dialog = SettingsTableDialog(JSON_FILE, "test setting")
    dialog.exec()
    sys.exit(app.exec())


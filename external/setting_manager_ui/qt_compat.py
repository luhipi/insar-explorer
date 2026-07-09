"""Qt binding compatibility helpers for setting_manager_ui.

This module keeps setting_manager_ui independent from host applications while
supporting QGIS PyQt, PyQt6, PyQt5, PySide6, and PySide2 where available.
"""

_BINDING_IMPORT_ERRORS = []

try:  # Prefer QGIS' Qt binding when embedded in QGIS.
    from qgis.PyQt.QtWidgets import (
        QApplication,
        QCheckBox,
        QColorDialog,
        QComboBox,
        QDialog,
        QDoubleSpinBox,
        QHBoxLayout,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
    from qgis.PyQt.QtCore import Qt, pyqtSignal as Signal
    from qgis.PyQt.QtGui import QBrush, QColor
except ImportError as exc:
    _BINDING_IMPORT_ERRORS.append(exc)
    try:
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QColorDialog,
            QComboBox,
            QDialog,
            QDoubleSpinBox,
            QHBoxLayout,
            QLineEdit,
            QMessageBox,
            QPushButton,
            QSizePolicy,
            QSpinBox,
            QTableWidget,
            QTableWidgetItem,
            QTabWidget,
            QVBoxLayout,
            QWidget,
        )
        from PyQt6.QtCore import Qt, pyqtSignal as Signal
        from PyQt6.QtGui import QBrush, QColor
    except ImportError as exc:
        _BINDING_IMPORT_ERRORS.append(exc)
        try:
            from PyQt5.QtWidgets import (
                QApplication,
                QCheckBox,
                QColorDialog,
                QComboBox,
                QDialog,
                QDoubleSpinBox,
                QHBoxLayout,
                QLineEdit,
                QMessageBox,
                QPushButton,
                QSizePolicy,
                QSpinBox,
                QTableWidget,
                QTableWidgetItem,
                QTabWidget,
                QVBoxLayout,
                QWidget,
            )
            from PyQt5.QtCore import Qt, pyqtSignal as Signal
            from PyQt5.QtGui import QBrush, QColor
        except ImportError as exc:
            _BINDING_IMPORT_ERRORS.append(exc)
            try:
                from PySide6.QtWidgets import (
                    QApplication,
                    QCheckBox,
                    QColorDialog,
                    QComboBox,
                    QDialog,
                    QDoubleSpinBox,
                    QHBoxLayout,
                    QLineEdit,
                    QMessageBox,
                    QPushButton,
                    QSizePolicy,
                    QSpinBox,
                    QTableWidget,
                    QTableWidgetItem,
                    QTabWidget,
                    QVBoxLayout,
                    QWidget,
                )
                from PySide6.QtCore import Qt, Signal
                from PySide6.QtGui import QBrush, QColor
            except ImportError as exc:
                _BINDING_IMPORT_ERRORS.append(exc)
                try:
                    from PySide2.QtWidgets import (
                        QApplication,
                        QCheckBox,
                        QColorDialog,
                        QComboBox,
                        QDialog,
                        QDoubleSpinBox,
                        QHBoxLayout,
                        QLineEdit,
                        QMessageBox,
                        QPushButton,
                        QSizePolicy,
                        QSpinBox,
                        QTableWidget,
                        QTableWidgetItem,
                        QTabWidget,
                        QVBoxLayout,
                        QWidget,
                    )
                    from PySide2.QtCore import Qt, Signal
                    from PySide2.QtGui import QBrush, QColor
                except ImportError as final_exc:
                    _BINDING_IMPORT_ERRORS.append(final_exc)
                    raise ImportError(
                        "setting_manager_ui requires qgis.PyQt, PyQt6, PyQt5, "
                        "PySide6, or PySide2."
                    ) from final_exc


def _enum_value(owner, enum_name, value_name, legacy_name=None):
    """Return a Qt6 scoped enum value when available, otherwise a Qt5 alias."""
    enum_owner = getattr(owner, enum_name, None)
    if enum_owner is not None and hasattr(enum_owner, value_name):
        return getattr(enum_owner, value_name)
    return getattr(owner, legacy_name or value_name)


ITEM_IS_EDITABLE = _enum_value(Qt, "ItemFlag", "ItemIsEditable")
DONT_USE_NATIVE_DIALOG = _enum_value(
    QColorDialog,
    "ColorDialogOption",
    "DontUseNativeDialog",
)
SIZE_POLICY_MINIMUM = _enum_value(QSizePolicy, "Policy", "Minimum")
SIZE_POLICY_EXPANDING = _enum_value(QSizePolicy, "Policy", "Expanding")

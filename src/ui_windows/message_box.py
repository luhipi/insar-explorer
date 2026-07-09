from qgis.PyQt.QtWidgets import QMessageBox
from ..qt_compat import (
    MESSAGE_BUTTON_OK,
    MESSAGE_ICON_CRITICAL,
    MESSAGE_ICON_INFORMATION,
    MESSAGE_ICON_WARNING,
    exec_dialog,
)


class MessageBox:
    def __init__(self, message, title="Information"):
        self.message = message
        self.title = title
        self.wgt = QMessageBox()
        self.wgt.setWindowTitle(self.title)
        # self.wgt.setText(self.message)
        self.wgt.setText(f"<html><body>{self.message}</body></html>")
        self.addButtons()
        self.setStyle()
        self._exec()

    def _exec(self):
        exec_dialog(self.wgt)

    def setStyle(self):
        self.wgt.setIcon(MESSAGE_ICON_INFORMATION)

    def addButtons(self):
        self.wgt.setStandardButtons(MESSAGE_BUTTON_OK)


class InfoBox(MessageBox):
    def __init__(self, message, title="Information"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(MESSAGE_ICON_INFORMATION)


class ErrorBox(MessageBox):
    def __init__(self, message, title="Error"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(MESSAGE_ICON_CRITICAL)


class WarningBox(MessageBox):
    def __init__(self, message, title="Warning"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(MESSAGE_ICON_WARNING)

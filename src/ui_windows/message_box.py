from qgis.PyQt.QtWidgets import QMessageBox


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
        self.wgt.exec()

    def setStyle(self):
        self.wgt.setIcon(QMessageBox.Icon.Information)

    def addButtons(self):
        self.wgt.setStandardButtons(QMessageBox.StandardButton.Ok)


class InfoBox(MessageBox):
    def __init__(self, message, title="Information"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(QMessageBox.Icon.Information)


class ErrorBox(MessageBox):
    def __init__(self, message, title="Error"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(QMessageBox.Icon.Critical)


class WarningBox(MessageBox):
    def __init__(self, message, title="Warning"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(QMessageBox.Icon.Warning)

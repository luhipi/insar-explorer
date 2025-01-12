from PyQt5.QtWidgets import QMessageBox


class MessageBox:
    def __init__(self, message, title="Information"):
        self.message = message
        self.title = title
        self.wgt = QMessageBox()
        self.wgt.setWindowTitle(self.title)
        self.wgt.setText(self.message)
        self.addButtons()
        self.setStyle()
        self.wgt.exec_()

    def setStyle(self):
        self.wgt.setIcon(QMessageBox.Information)

    def addButtons(self):
        self.wgt.setStandardButtons(QMessageBox.Ok)


class InfoBox(MessageBox):
    def __init__(self, message, title="Information"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(QMessageBox.Information)


class ErrorBox(MessageBox):
    def __init__(self, message, title="Error"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(QMessageBox.Critical)


class WarningBox(MessageBox):
    def __init__(self, message, title="Warning"):
        super().__init__(message, title=title)

    def setStyle(self):
        self.wgt.setIcon(QMessageBox.Warning)

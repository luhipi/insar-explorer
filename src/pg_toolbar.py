from qgis.PyQt.QtWidgets import QAction, QToolBar

from qgis.PyQt.QtWidgets import QPushButton

class CustomToolbar(QToolBar):
    """Small pyqtgraph toolbar for time-series plots."""

    def __init__(self, plot_widget, parent):
        super().__init__(parent)
        self.plot_widget = plot_widget
        self.setStyleSheet("""
            QToolBar {
                background: #f0f0f0;
                border: 1px solid #dcdcdc;
                min-height: 20px;
                max-height: 20px;
            }
            QToolButton {
                background: #e0e0e0;
                border: 1px solid #b0b0b0;
                padding: 0px;
                margin: 0px;
            }
            QToolButton:pressed {
                background: #d0d0d0;
            }
        """)

        # add action or push button
        # reset_action = QAction("Reset View", self)
        # self.addAction(reset_action)

        # btn = QPushButton("Button", self)
        # self.addWidget(btn)


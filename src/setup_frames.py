from ..external import pyqtgraph as pg

from qgis.PyQt.QtWidgets import QVBoxLayout

from .pg_toolbar import CustomToolbar


def setupTsFrame(ui):
    ui.plot_widget = pg.GraphicsLayoutWidget(parent=ui.frame_plot_ts)
    ui.plot_widget.setBackground('w')
    ui.plot_widget.plot_items = []
    ui.toolbar = CustomToolbar(ui.plot_widget, ui.frame_plot_ts)

    ui.frame_plot_layout = QVBoxLayout(ui.frame_plot_ts)
    ui.frame_plot_layout.addWidget(ui.plot_widget)
    ui.frame_plot_layout.addWidget(ui.toolbar)

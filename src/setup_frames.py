from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from qgis.PyQt.QtWidgets import QVBoxLayout

from .mpl_toolbar import CustomToolbar


def setupTsFrame(ui):
    print(ui)
    plt.style.use('bmh')
    ui.figure = Figure()
    ui.canvas = FigureCanvas(ui.figure)
    ui.toolbar = CustomToolbar(ui.canvas, ui.frame_plot_ts)

    ui.frame_plot_layout = QVBoxLayout(ui.frame_plot_ts)
    ui.frame_plot_layout.addWidget(ui.canvas)
    ui.frame_plot_layout.addWidget(ui.toolbar)


# from PyQt5.QtWebKitWidgets import QWebView
# from PyQt5.QtWidgets import QVBoxLayout
#
# def setupTsFrame(ui):
#     """
#     Setup the time series frame to contain the plot
#     """
#     ui.web_view = QWebView()
#     ui.frame_plot_layout = QVBoxLayout(ui.frame_plot_ts)
#     ui.frame_plot_layout.addWidget(ui.web_view)

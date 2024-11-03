from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from qgis.PyQt.QtWidgets import QVBoxLayout


def setupTsFrame(ui):
    print(ui)
    ui.figure = Figure()
    ui.canvas = FigureCanvas(ui.figure)
    ui.frame_plot_layout = QVBoxLayout(ui.frame_plot_ts)
    ui.frame_plot_layout.addWidget(ui.canvas)


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

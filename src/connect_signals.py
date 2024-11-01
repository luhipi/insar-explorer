from . import plot_timeseries as pts


def connect_signals(ui):
    ui.pb_choose_point.clicked.connect(lambda: pts.plotTs(ui))



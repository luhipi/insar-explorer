import os

import numpy as np
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import timedelta

from .model_fitting import FittingModels
from .setting_manager_ui.json_settings import JsonSettings

class PlotTs():

    def __init__(self, ui):
        self.ui = ui
        self.ax = None
        self.dates = None
        self.ts_values = 0
        self.ref_values = 0
        self.plot_values = None
        self.residuals_values = None
        script_path = os.path.abspath(__file__)
        json_file = "config.json"
        self.config_file = os.path.join(os.path.dirname(script_path), 'config', json_file)
        self.fit_plot_list = []
        self.fit_models = []
        self.fit_seasonal_flag = False
        self.replicate_flag = False
        self.plot_replicates = []
        self.replicate_value = 5.6/2
        self.ax_residuals = None
        self.plot_residuals_flag = False
        self.plot_residuals_list = []
        self.parms = {}
        self.updateSettings()

    def updateSettings(self):
        parms_ts = JsonSettings(self.config_file)
        parms_ts.load("timeseries settings")

        parms = {}
        parms['title'] = parms_ts.get(["time series plot", "title"]) or ""
        parms['xlabel'] = parms_ts.get(["time series plot", "xlabel"]) or ""
        parms['ylabel'] = parms_ts.get(["time series plot", "ylabel"]) or ""
        parms['marker'] = parms_ts.get(["time series plot", "marker"]) or "."
        parms['marker color'] = parms_ts.get(["time series plot", "marker color"]) or None
        parms['marker size'] = parms_ts.get(["time series plot", "marker size"])
        parms['line style'] = parms_ts.get(["time series plot", "line style"]) or ''
        parms['line color'] = parms_ts.get(["time series plot", "line color"]) or None
        parms['line width'] = parms_ts.get(["time series plot", "line width"])

        parms['ymin'] = parms_ts.get(["time series plot", "ymin"])
        parms['ymax'] = parms_ts.get(["time series plot", "ymax"])

        # replica
        parms['replica up color'] = parms_ts.get(["time series plot", "replica up color"]) or 'gray'
        parms['replica down color'] = parms_ts.get(["time series plot", "replica down color"]) or 'gray'
        parms['replica marker size'] = parms_ts.get(["time series plot", "replica marker size"]) or 5
        parms['replica marker'] = parms_ts.get(["time series plot", "replica marker"]) or 'o'

        self.parms['time series plot'] = parms

        # export settings
        parms = {}
        parms['dpi'] = parms_ts.get(["export", "dpi"]) or 300
        parms['pad'] = parms_ts.get(["export", "pad"]) or 0.1

        self.parms['export'] = parms

    def clear(self):
        self.ui.figure.clear()
        self.ui.canvas.draw()

    def prepareTsValues(self, *, dates, ts_values=None, ref_values=None):
        if dates is not None:
            self.dates = dates

        if ts_values is not None:
            self.ts_values = ts_values

        if ref_values is not None:
            self.ref_values = ref_values

        self.plot_values = self.ts_values - self.ref_values

    def initializeAxes(self):
        self.ui.figure.clear()
        self.updateSettings()
        if self.plot_residuals_flag:
            self.ax = self.ui.figure.add_subplot(211)
            self.ax_residuals = self.ui.figure.add_subplot(212)
        else:
            self.ax = self.ui.figure.add_subplot(111)

    def plotTs(self, *, dates=None, ts_values=None, ref_values=None, marker=None):
        self.initializeAxes()

        if marker is None:
            marker = self.parms['time series plot']['marker']

        self.prepareTsValues(dates=dates, ts_values=ts_values, ref_values=ref_values)
        if self.dates is None:
            return

        parms = self.parms['time series plot']
        marker_size = parms['marker size']
        marker_color = parms['marker color']
        line_style = parms['line style']
        line_color = parms['line color']
        line_width = parms['line width']

        self.ax.scatter(self.dates, self.plot_values, marker=marker, s=marker_size, c=marker_color)
        if line_style:
            self.ax.plot(self.dates, self.plot_values, line_style, color=line_color, linewidth=line_width)
        if self.replicate_flag:
            marker_up_color = parms['replica up color']
            marker_down_color = parms['replica down color']
            marker_size_replica = parms['replica marker size']
            marker_replica = parms['replica marker']
            replicate_up = self.ax.scatter(self.dates, self.plot_values + self.replicate_value,
                                           marker=marker_replica, c=marker_up_color, s=marker_size_replica)
            replicate_dn = self.ax.scatter(self.dates, self.plot_values - self.replicate_value,
                                             marker=marker_replica, c=marker_down_color, s=marker_size_replica)
            self.plot_replicates.append([replicate_up, replicate_dn])
        self.decoratePlot()
        self.fitModel()
        self.ui.canvas.draw()

    def fitModel(self):
        [plot.remove() for plot in self.fit_plot_list]
        self.ui.canvas.draw_idle()
        self.fit_plot_list = []
        if self.plot_values is None:
            return
        if self.fit_models is []:
            return

        fit_line_type = '--'
        fit_line_color = 'black'
        fit_seasonal = self.fit_seasonal_flag
        for fit_model in self.fit_models:
            model_values, model_x, model_y = (
                FittingModels(self.dates, self.plot_values, model=fit_model).fit(seasonal=fit_seasonal))
            plot = self.ax.plot(model_x, model_y, fit_line_type, color=fit_line_color)
            self.fit_plot_list.append(plot[0])
            self.ui.canvas.draw_idle()

            self.residuals_values = self.plot_values - model_values
            self.plotResiduals()

    def plotResiduals(self):
        [plot.remove() for plot in self.plot_residuals_list]
        self.plot_residuals_list = []
        if self.plot_residuals_flag:
            plot_residual = self.ax_residuals.plot(self.dates, self.residuals_values, self.residual_markers,
                                                   color='C2')
            self.plot_residuals_list.append(plot_residual[0])
            self.decoratePlot(ax=self.ax_residuals)
            self.ui.canvas.draw_idle()

    def decoratePlot(self, ax=None):
        if not ax:
            ax = self.ax
        # First set lims then ticks
        self.setXlims(ax=ax)
        self.setXticks(ax=ax)
        self.setYlims(ax=ax)
        self.setYticks(ax=ax)
        self.setGrid(status=True, ax=ax)
        self.setLabels(ax=ax)
        self.ui.figure.tight_layout()

    def setGrid(self, status, ax=None):
        if not ax:
            ax = self.ax
        ax.grid(status)

    def setLabels(self, ax=None):
        if not ax:
            ax = self.ax

        title = self.parms['time series plot']['title']
        if title != "":
            ax.set_title(title)

        label = self.parms['time series plot']['xlabel']
        if label != "":
            ax.set_xlabel(label)

        label = self.parms['time series plot']['ylabel']
        if label != "":
            ax.set_ylabel(label)

    def setXticks(self, ax=None):
        if not ax:
            ax = self.ax
        min_date = np.nanmin(self.dates)
        max_date = np.nanmax(self.dates)
        date_range = (max_date - min_date).days

        if date_range >= 1461:
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 7]))
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        elif date_range >= 366:
            ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
            ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
            ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))

    def setYticks(self, ax=None):
        if not ax:
            ax = self.ax

        y_min, y_max = ax.get_ylim()
        y_range = y_max - y_min

        ideal_intervals = (list(range(1,10, 1)) +
                           list(range(10, 100, 10)) +
                           list(range(100, 1000, 100)) +
                           list(range(1000, 10000, 1000)) +
                           list(range(10000, 100000, 10000)))

        ideal_i = np.argmin(np.abs(np.array(ideal_intervals) - y_range / 3))
        major_tick_interval = ideal_intervals[ideal_i]

        if major_tick_interval <= 10:
            minor_tick_interval = None
        elif major_tick_interval <= 100:
            minor_tick_interval = 10
        elif major_tick_interval <= 1000:
            minor_tick_interval = 100
        elif major_tick_interval <= 10000:
            minor_tick_interval = 1000
        else:
            minor_tick_interval = major_tick_interval / 5

        ax.yaxis.set_major_locator(ticker.MultipleLocator(major_tick_interval))
        if minor_tick_interval:
            ax.yaxis.set_minor_locator(ticker.MultipleLocator(minor_tick_interval))
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.0f}'))

    def setXlims(self, *, ax=None, use_data_xlim=True, padding=30):
        """
        Set the x-axis limits.

        :param use_data_xlim: bool
            If True, set the x-axis limits to the min and max of the data.
            If False, set the x-axis limits to the start and end of the year.
        :param padding: int
            Number of days to pad the x-axis limits.
        """
        if not ax:
            ax = self.ax
        min_date = np.nanmin(self.dates)
        max_date = np.nanmax(self.dates)

        if use_data_xlim:
            ax.set_xlim(min_date-timedelta(days=padding),
                             max_date+timedelta(days=padding))
        else:
            start_of_year = mdates.num2date(mdates.datestr2num(f'{min_date.year}-01-01'))
            end_of_year = mdates.num2date(mdates.datestr2num(f'{max_date.year+1}-01-01'))
            ax.set_xlim(start_of_year, end_of_year)

    def setYlims(self, ax=None):
        if not ax:
            ax = self.ax

        if ax == self.ax:
            y_min = np.nanmin(self.plot_values)
            y_max = np.nanmax(self.plot_values)
        elif ax == self.ax_residuals:
            y_max = np.nanmax(np.abs(self.residuals_values))
            y_min = -y_max

        y_range = y_max - y_min
        y_min_rounded = -5
        y_max_rounded = 5
        for i in [10000, 1000, 100, 10]:
            if y_range >= i:
                y_min_rounded = np.floor(y_min / i) * i
                y_max_rounded = np.ceil(y_max / i) * i
                break

        y_min_rounded = np.min([y_min_rounded, -5])
        y_max_rounded = np.max([y_max_rounded, 5])

        ax.set_ylim(y_min_rounded, y_max_rounded)

        ymin = self.parms['time series plot']['ymin']
        ymax = self.parms['time series plot']['ymax']
        import warnings
        warnings.warn(str(ymin))
        ax.set_ylim([ymin, ymax])  # TODO: check if works with ymax or ymin=None

    def savePlotAsImage(self, filename=None):
        parms = self.parms["export"]
        dpi = int(parms["dpi"])
        pad = parms["pad"]
        fig_size_export = (12, 6) if self.plot_residuals_flag else (12, 3)
        fig_size = self.ui.figure.get_size_inches()
        if filename:
            self.ui.figure.set_size_inches(fig_size_export)
            self.ui.figure.savefig(filename,
                                   dpi=dpi,
                                   bbox_inches='tight',
                                   transparent=False,
                                   pad_inches=pad)
            self.ui.figure.set_size_inches(fig_size)
            self.ui.canvas.draw()

# import plotly.graph_objs as go
# import plotly.io as pio
#
# def plotTs(ui):
#     """
#     Plot time series
#     """
#     fig = go.Figure(data=[go.Scatter(x=list(range(100)), y=np.random.random(100))])
#     fig.update_layout(margin=dict(l=0.1, r=0.1, t=0.1, b=0.1))
#     html = pio.to_html(fig, full_html=False)
#     ui.web_view.setHtml(html)
#

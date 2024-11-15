import numpy as np
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import datetime, timedelta

from .model_fitting import FittingModels

class PlotTs():

    def __init__(self, ui):
        self.ui = ui
        self.ax = None
        self.dates = None
        self.ts_values = 0
        self.ref_values = 0
        self.plot_values = None
        self.residuals_values = None
        self.marker = '.'
        self.residual_markers = '.'
        self.fit_plot_list = []
        self.fit_models = []
        self.fit_seasonal_flag = False
        self.replicate_flag = False
        self.plot_replicates = []
        self.replicate_value = 5.6/2
        self.ax_residuals = None
        self.plot_residuals_flag = False
        self.plot_residuals_list = []

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
        if self.plot_residuals_flag:
            self.ax = self.ui.figure.add_subplot(211)
            self.ax_residuals = self.ui.figure.add_subplot(212)
        else:
            self.ax = self.ui.figure.add_subplot(111)

    def plotTs(self, *, dates=None, ts_values=None, ref_values=None, marker=None, marker_replicate='.k'):
        if marker is None:
            marker = self.marker
        self.initializeAxes()

        self.prepareTsValues(dates=dates, ts_values=ts_values, ref_values=ref_values)

        self.ax.plot(self.dates, self.plot_values, marker)
        if self.replicate_flag:
            replicate_up = self.ax.plot(self.dates, self.plot_values + self.replicate_value,
                                        marker_replicate, color='gray')
            replicate_dn = self.ax.plot(self.dates, self.plot_values - self.replicate_value,
                                        marker_replicate, color='gray')
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

    def setGrid(self, status, ax=None):
        if not ax:
            ax = self.ax
        ax.grid(status)

    def setXticks(self, ax=None):
        if not ax:
            ax = self.ax
        min_date = np.min(self.dates)
        max_date = np.max(self.dates)
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
        ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.0f}'))
        ax.set_ylabel('[mm]')

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
        min_date = np.min(self.dates)
        max_date = np.max(self.dates)

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
            y_min = np.min(self.plot_values)
            y_max = np.max(self.plot_values)
        elif ax == self.ax_residuals:
            y_max = np.max(np.abs(self.residuals_values))
            y_min = -y_max

        y_min_rounded = np.floor(y_min / 5) * 5
        y_max_rounded = np.ceil(y_max / 5) * 5
        ax.set_ylim(y_min_rounded, y_max_rounded)


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

import os
import sys

import numpy as np
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import timedelta

from .model_fitting import FittingModels
from ..external.setting_manager_ui.json_settings import JsonSettings

sys.path.insert(0, os.path.abspath('../..'))
try:
    from insar_explorer import __version__
except ImportError:
    __version__ = "xx.xx.xx"


class PlotTs():

    def __init__(self, ui):
        self.ui = ui
        self.ax = None
        self.dates = None
        self.ts_values = 0
        self.ref_values = 0
        self.plot_values = None
        self.plot_multiple_values = None
        self.min_plot_values = None
        self.max_plot_values = None
        self.residuals_values = None
        script_path = os.path.abspath(__file__)
        json_file = "config.json"
        self.config_file = os.path.join(os.path.dirname(script_path), 'config', json_file)
        self.plot_data_list = []
        self.plot_list = []
        self.fit_models = []
        self.fit_seasonal_flag = False
        self.replicate_flag = False
        self.plot_y_axis = "from_data"
        self.replicate_value = 5.6 / 2
        self.ax_residuals = None
        self.plot_residuals_flag = False
        self.plot_residuals_list = []
        self.hold_on_flag = False
        self.random_marker_color_flag = False
        self.parms = {}
        self.updateSettings()
        self.coords = None
        self.ref_coords = None

    def modifySettings(self, block_key, value):
        params = JsonSettings(self.config_file)
        params.save(block_key, value)

    def updateSettings(self):
        parms_ts = JsonSettings(self.config_file)
        parms_ts.load("timeseries settings")

        parms = {}
        parms['title'] = parms_ts.get(["time series plot", "title"]) or ""
        parms['xlabel'] = parms_ts.get(["time series plot", "xlabel"]) or ""
        parms['ylabel'] = parms_ts.get(["time series plot", "ylabel"]) or ""
        parms['font size'] = parms_ts.get(["time series plot", "font size"]) or 12
        parms['marker'] = parms_ts.get(["time series plot", "marker"]) or "."
        parms['marker color'] = parms_ts.get(["time series plot", "marker color"]) or None
        parms['marker alpha'] = parms_ts.get(["time series plot", "marker alpha"]) or 1.0
        parms['marker edge color'] = parms_ts.get(["time series plot", "marker edge color"]) or None
        parms['marker size'] = parms_ts.get(["time series plot", "marker size"])
        parms['line style'] = parms_ts.get(["time series plot", "line style"]) or ''
        parms['line color'] = parms_ts.get(["time series plot", "line color"]) or None
        parms['line alpha'] = parms_ts.get(["time series plot", "line alpha"]) or 1.0
        parms['line width'] = parms_ts.get(["time series plot", "line width"]) or 1

        parms['series fill color'] = parms_ts.get(["time series plot", "series fill color"]) or 'blue'
        parms['series fill alpha'] = parms_ts.get(["time series plot", "series fill alpha"]) or 0.2
        parms['series line style'] = parms_ts.get(["time series plot", "series line style"]) or ''
        parms['series line color'] = parms_ts.get(["time series plot", "series line color"]) or None
        parms['series line alpha'] = parms_ts.get(["time series plot", "series line alpha"]) or 1.0
        parms['series line width'] = parms_ts.get(["time series plot", "series line width"]) or 0.2

        parms['ymin'] = parms_ts.get(["time series plot", "ymin"])
        parms['ymax'] = parms_ts.get(["time series plot", "ymax"])
        parms['grid'] = parms_ts.get(["time series plot", "grid"])
        parms['background color'] = parms_ts.get(["time series plot", "background color"]) or 'white'
        parms['date format'] = parms_ts.get(["time series plot", "date format"]) or None

        # replica
        parms['replica color 1'] = parms_ts.get(["time series plot", "replica color 1"]) or 'gray'
        parms['replica color 2'] = parms_ts.get(["time series plot", "replica color 2"]) or 'gray'
        parms['replica alpha'] = parms_ts.get(["time series plot", "replica alpha"]) or 1.0
        parms['replica marker size'] = parms_ts.get(["time series plot", "replica marker size"]) or 5
        parms['replica marker'] = parms_ts.get(["time series plot", "replica marker"]) or 'o'
        parms['number of up replicas'] = parms_ts.get(["time series plot", "number of up replicas"])
        parms['number of down replicas'] = parms_ts.get(["time series plot", "number of down replicas"])

        self.parms['time series plot'] = parms

        # figure settings
        parms = {}
        parms['background color'] = parms_ts.get(["figure", "background color"]) or 'white'

        self.parms['figure'] = parms

        # export settings
        parms = {}
        parms['dpi'] = parms_ts.get(["export", "dpi"]) or 300
        parms['pad'] = parms_ts.get(["export", "pad"]) or 0.1

        self.parms['export'] = parms

        # residual plot
        parms = {}
        parms['title'] = parms_ts.get(["residual plot", "title"]) or ""
        parms['xlabel'] = parms_ts.get(["residual plot", "xlabel"]) or ""
        parms['ylabel'] = parms_ts.get(["residual plot", "ylabel"]) or ""
        parms['marker'] = parms_ts.get(["residual plot", "marker"]) or "."
        parms['marker color'] = parms_ts.get(["residual plot", "marker color"]) or None
        parms['marker alpha'] = parms_ts.get(["residual plot", "marker alpha"]) or 1.0
        parms['marker edge color'] = parms_ts.get(["residual plot", "marker edge color"]) or None
        parms['marker size'] = parms_ts.get(["residual plot", "marker size"])
        parms['line style'] = parms_ts.get(["residual plot", "line style"]) or ''
        parms['line color'] = parms_ts.get(["residual plot", "line color"]) or None
        parms['line alpha'] = parms_ts.get(["residual plot", "line alpha"]) or 1.0
        parms['line width'] = parms_ts.get(["residual plot", "line width"])
        parms['ymin'] = parms_ts.get(["residual plot", "ymin"])
        parms['ymax'] = parms_ts.get(["residual plot", "ymax"])

        # other parameters from time series plot
        parms['grid'] = parms_ts.get(["time series plot", "grid"])
        parms['background color'] = parms_ts.get(["time series plot", "background color"]) or 'white'
        parms['font size'] = parms_ts.get(["time series plot", "font size"]) or 12
        parms['date format'] = parms_ts.get(["time series plot", "date format"]) or None
        self.parms['residual plot'] = parms

    def clear(self):
        if not self.hold_on_flag:
            self.ui.figure.clear()
        self.ui.canvas.draw()
        self.dates = None
        self.ts_values = 0
        self.ref_values = 0
        self.plot_list = []
        self.plot_data_list = []

    def prepareTsValues(self, *, dates, ts_values=None, ref_values=None):
        if dates is not None:
            sort_idx = np.argsort(dates)
            self.dates = dates[sort_idx]
        else:
            sort_idx = None

        def prepareValues(values, sort_idx=None):
            if values is not None:
                values = np.array(values, dtype=float, ndmin=2)
                if values.shape[0] == 1:
                    values = values.T
                if values.shape[0] > 1 and sort_idx is not None:
                    values = values[sort_idx, :]
            else:
                values = np.zeros((len(self.dates), 1))
            return values

        if ts_values is None:
            ts_values = self.ts_values
        if ref_values is None:
            ref_values = self.ref_values

        self.ts_values = prepareValues(ts_values, sort_idx)
        self.ref_values = prepareValues(ref_values, sort_idx)
        self.preparePlotValues()

    def preparePlotValues(self):
        plot_values = self.ts_values - np.mean(self.ref_values, axis=1, keepdims=True)

        if np.shape(self.ts_values)[1] > 1:
            # actual data range
            self.min_plot_values = np.min(plot_values, axis=1)
            self.max_plot_values = np.max(plot_values, axis=1)
            # based on std
            # self.min_plot_values = np.mean(plot_values, axis=1) - np.std(plot_values, axis=1)
            # self.max_plot_values = np.mean(plot_values, axis=1) + np.std(plot_values, axis=1)
            self.plot_multiple_values = plot_values
        else:
            self.min_plot_values = None
            self.max_plot_values = None
            self.plot_multiple_values = None
        self.plot_values = np.mean(self.ts_values, axis=1) - np.mean(self.ref_values, axis=1)

    def initializeAxes(self):
        """
        Initialize the axes for the plot.
        :param update: bool
            If True, clear the latest plot.
        """
        if not self.hold_on_flag:
            self.ui.figure.clear()
            self.ax = None
            self.ax_residuals = None
            self.plot_list = []
            self.plot_data_list = []
            self.plot_residuals_list = []

        if self.plot_residuals_flag:
            if self.ax and not self.ax_residuals:
                # convert ax from subplot(111) to subplot(211) and preserve content
                self.ui.figure.clear()
                self.ax = self.ui.figure.add_subplot(211)
                self.ax_residuals = self.ui.figure.add_subplot(212)
            else:
                if not self.ax:
                    self.ax = self.ui.figure.add_subplot(211)
                if not self.ax_residuals:
                    self.ax_residuals = self.ui.figure.add_subplot(212)
        else:
            if self.ax and self.ax_residuals:
                # convert ax from subplot(211) to subplot(111) and preserve content
                self.ui.figure.clear()
                self.ax = self.ui.figure.add_subplot(111)
                self.ax_residuals = None
            elif not self.ax:
                self.ax = self.ui.figure.add_subplot(111)

    def plotTs(self, *, dates=None, ts_values=None, ref_values=None, plot_multiple=True, coords=None, ref_coords=None,
               update=False):
        # update: flag incicating if the plot should be updated or a new one created

        plot_dict = {}
        self.updateSettings()

        if update:
            if len(self.plot_list) == 0:
                return
            self.removeLastPlot(update=update)
            random_marker_color_flag = False
        else:
            random_marker_color_flag = self.random_marker_color_flag

        self.initializeAxes()

        # coords
        if ts_values is not None:
            self.coords = coords
        if ref_values is not None:
            self.ref_coords = ref_coords

        self.prepareTsValues(dates=dates, ts_values=ts_values, ref_values=ref_values)

        if self.dates is None:
            return

        # check if there is any finite value in the plot_values
        plot_values = np.array(self.plot_values, dtype=np.float64)
        if np.sum(np.isfinite(plot_values)) == 0:
            return

        if random_marker_color_flag:
            rand_color = np.random.rand(3, )
            self.parms['time series plot']['marker color'] = self.parms['time series plot']['line color'] = rand_color
        plot_data_dict = {'dates': self.dates, 'ts_values': self.ts_values, 'ref_values': self.ref_values,
                          'param': self.parms, 'coords': self.coords, 'ref_coords': self.ref_coords}

        parms = self.parms['time series plot']
        marker = parms['marker']
        marker_size = parms['marker size']
        marker_color = parms['marker color']
        marker_alpha = parms['marker alpha']
        edge_color = parms['marker edge color']
        line_style = parms['line style']
        line_color = parms['line color']
        line_alpha = parms['line alpha']
        line_width = parms['line width']

        if plot_multiple and self.min_plot_values is not None:
            lower_bound = self.min_plot_values
            upper_bound = self.max_plot_values
            series_fill_color = parms['series fill color']
            series_fill_alpha = parms['series fill alpha']
            plot_fill_between = self.ax.fill_between(self.dates, lower_bound, upper_bound, color=series_fill_color,
                                                     alpha=series_fill_alpha)
        else:
            plot_fill_between = None
        plot_dict['plot_multiple_fill'] = plot_fill_between

        if self.plot_multiple_values is not None:
            series_line_style = parms['series line style']
            series_line_color = parms['series line color']
            series_line_alpha = parms['series line alpha']
            series_line_width = parms['series line width']
            if series_line_style:
                plot_multiple_lines = self.ax.plot(self.dates, self.plot_multiple_values, series_line_style,
                                                   color=series_line_color, linewidth=series_line_width,
                                                   alpha=series_line_alpha)
            else:
                plot_multiple_lines = [None]
        else:
            plot_multiple_lines = [None]
        plot_dict['plot_multiple_lines'] = plot_multiple_lines

        if marker_size > 0:
            plot = self.ax.scatter(self.dates, self.plot_values, marker=marker, s=marker_size, c=marker_color,
                                   alpha=marker_alpha, edgecolors=edge_color, linewidth=0.2)
        else:
            plot = None
        plot_dict['scatter'] = plot

        # update ylim for hold on
        self.updateYlim(ax=self.ax, y_data=self.plot_values)

        if line_style != '':
            plot_line = self.ax.plot(self.dates, self.plot_values, line_style, color=line_color, linewidth=line_width,
                                     alpha=line_alpha)
        else:
            plot_line = [None]
        plot_dict['line'] = plot_line[0]

        if self.replicate_flag:
            replicate_up_list, replicate_dn_list = self.plotReplicas()
        else:
            replicate_up_list, replicate_dn_list = [None], [None]
        plot_dict['replicate_up'] = replicate_up_list
        plot_dict['replicate_dn'] = replicate_dn_list

        self.decoratePlot(parms=parms)
        fit_plot_list = self.fitModel()
        plot_dict['fit_plot_list'] = fit_plot_list

        parms_figure = self.parms['figure']
        self.decorateFigure(parms=parms_figure)

        self.plot_data_list.append(plot_data_dict)
        self.plot_list.append(plot_dict)

        self.ui.canvas.draw()

    def removeLastPlot(self, n=1, update=False):
        if update or len(self.plot_list) == 1:
            idx = -n
        else:
            idx = -n - 1

        if len(self.plot_list) < n:
            return False

        plot_data_dict = self.plot_data_list[idx]
        params = plot_data_dict['param'] or None
        if len(plot_data_dict['dates']) == 1:
            dates = None
            ts_values = 0
            ref_values = 0
            coords = None
            ref_coords = None
        else:
            dates = plot_data_dict['dates']
            ts_values = plot_data_dict['ts_values']
            ref_values = plot_data_dict['ref_values']
            coords = plot_data_dict['coords']
            ref_coords = plot_data_dict['ref_coords']

        self.dates = dates
        self.ts_values = ts_values
        self.ref_values = ref_values
        self.coords = coords
        self.ref_coords = ref_coords

        self.parms = params

        for _ in range(n):
            if len(self.plot_list) > 0:
                plot_dict = self.plot_list[-1]
                self.plot_list.pop()
                plot = plot_dict.get('scatter', None)
                if plot:
                    plot.remove()

                plot_line = plot_dict.get('line', None)
                if plot_line:
                    plot_line.remove()

                plot_multiple_fill = plot_dict.get('plot_multiple_fill', None)
                if plot_multiple_fill:
                    plot_multiple_fill.remove()

                plot_multiple_lines = plot_dict.get('plot_multiple_lines', None)
                for plot in plot_multiple_lines:
                    if plot:
                        plot.remove()

                plot_replica_up = plot_dict.get('replicate_up', None)
                for plot in plot_replica_up:
                    if plot:
                        plot.remove()

                plot_replica_dn = plot_dict.get('replicate_dn', None)
                for plot in plot_replica_dn:
                    if plot:
                        plot.remove()

                fit_plot_list = plot_dict.get('fit_plot_list', None)
                if fit_plot_list:
                    fit_plot_list.remove()

                res_plots = self.plot_residuals_list[-1]
                residual_scatter = res_plots['residual_scatter']
                residual_line = res_plots['residual_line']
                if residual_scatter:
                    residual_scatter.remove()
                if residual_line:
                    residual_line.remove()
                self.plot_residuals_list.pop()

                self.plot_data_list.pop()

        self.ui.canvas.draw()
        return True

    def plotReplicas(self):
        parms = self.parms['time series plot']
        marker_color_1 = parms['replica color 1']  # replica up
        marker_color_2 = parms['replica color 2']  # replica down
        marker_alpha = parms['replica alpha']
        marker_size_replica = parms['replica marker size']
        marker_replica = parms['replica marker']
        number_of_up_replicas = parms['number of up replicas']
        number_of_down_replicas = parms['number of down replicas']

        # plot multiple replicas
        replicate_up_list = []
        for i in range(number_of_up_replicas):
            replicate_value = self.replicate_value * (i + 1)

            if i % 2 == 0:
                marker_replica_color = marker_color_1
            else:
                marker_replica_color = marker_color_2

            replicate_up = self.ax.scatter(self.dates, self.plot_values + replicate_value, marker=marker_replica,
                                           c=marker_replica_color, s=marker_size_replica, alpha=marker_alpha)
            replicate_up_list.append(replicate_up)

        self.updateYlim(ax=self.ax, y_data=self.plot_values + replicate_value)

        replicate_dn_list = []
        for i in range(number_of_down_replicas):
            replicate_value = self.replicate_value * (i + 1)

            if i % 2 == 0:
                marker_replica_color = marker_color_2
            else:
                marker_replica_color = marker_color_1

            replicate_dn = self.ax.scatter(self.dates, self.plot_values - replicate_value, marker=marker_replica,
                                           c=marker_replica_color, s=marker_size_replica, alpha=marker_alpha)
            replicate_dn_list.append(replicate_dn)

        self.updateYlim(ax=self.ax, y_data=self.plot_values - replicate_value)

        return replicate_up_list, replicate_dn_list

    def fitModel(self):
        if self.plot_values is None:
            return
        if self.dates is None:
            return
        if self.fit_models is []:
            self.plot_residuals_list.append({'residual_scatter': None, 'residual_line': None})
            return

        fit_line_type = '--'
        fit_line_color = 'black'
        fit_seasonal = self.fit_seasonal_flag
        if len(self.fit_models) != 1:
            self.plot_residuals_list.append({'residual_scatter': None, 'residual_line': None})
            return
        else:
            fit_model = self.fit_models[0]
            model_values, model_x, model_y = (
                FittingModels(self.dates, self.plot_values, model=fit_model).fit(seasonal=fit_seasonal))
            fit_plot = self.ax.plot(model_x, model_y, fit_line_type, color=fit_line_color)
            self.ui.canvas.draw_idle()

            self.residuals_values = self.plot_values - model_values
            self.plotResiduals()

        return fit_plot[0]

    def plotResiduals(self):
        plot_dict = {'residual_scatter': None, 'residual_line': None}
        if self.plot_residuals_flag:
            parms = self.parms['residual plot']
            marker = parms['marker']
            marker_size = parms['marker size']
            marker_color = parms['marker color']
            marker_alpha = parms['marker alpha']
            edge_color = parms['marker edge color']
            line_style = parms['line style']
            line_color = parms['line color']
            line_alpha = parms['line alpha']
            line_width = parms['line width']

            plot_residual = self.ax_residuals.scatter(self.dates, self.residuals_values, marker=marker, c=marker_color,
                                                      s=marker_size, edgecolors=edge_color, alpha=marker_alpha)
            plot_dict['residual_scatter'] = plot_residual
            if line_style:
                plot_residual_line = self.ax_residuals.plot(self.dates, self.residuals_values, line_style,
                                                            color=line_color, linewidth=line_width, alpha=line_alpha)
                plot_dict['residual_line'] = plot_residual_line[0]
            self.decoratePlot(ax=self.ax_residuals, parms=parms)
            self.ui.canvas.draw_idle()

        self.plot_residuals_list.append(plot_dict)

    def decorateFigure(self, parms={}):
        self.setFigureStyle(parms=parms)

    def decoratePlot(self, ax=None, parms={}):
        if not ax:
            ax = self.ax
        # First set lims then ticks
        self.setFontSize(ax=ax, parms=parms)
        self.setXlims(ax=ax)
        self.setXticks(ax=ax, parms=parms)
        self.setYlims(ax=ax, parms=parms)
        self.setYticks(ax=ax)
        self.setGrid(ax=ax, parms=parms)
        self.setLabels(ax=ax, parms=parms)
        self.setAxisStyle(ax=ax, parms=parms)
        self.ui.figure.tight_layout()

    def setFontSize(self, ax=None, parms={}):
        if not ax:
            ax = self.ax
        font_size = parms['font size']
        ax.tick_params(axis='both', which='major', labelsize=font_size)
        ax.tick_params(axis='both', which='minor', labelsize=font_size)

    def setGrid(self, ax=None, parms={}):
        if not ax:
            ax = self.ax
        grid_type = parms['grid']

        ax.grid(False)
        if grid_type == 'horizontal':
            ax.grid(True, axis='y')
        elif grid_type == 'vertical':
            ax.grid(True, axis='x')
        elif grid_type == 'both':
            ax.grid(True)
        else:
            ax.grid(False)

    def setLabels(self, ax=None, parms={}):
        if not ax:
            ax = self.ax

        font_size = parms['font size']
        title = parms['title']
        if title != "":
            ax.set_title(title, fontsize=font_size)

        label = parms['xlabel']
        if label != "":
            ax.set_xlabel(label, fontsize=font_size)

        label = parms['ylabel']
        if label != "":
            ax.set_ylabel(label, fontsize=font_size)

    def setXticks(self, ax=None, parms={}):
        if not ax:
            ax = self.ax
        date_format = parms['date format']

        min_date = np.nanmin(self.dates)
        max_date = np.nanmax(self.dates)
        date_range = (max_date - min_date).days

        if date_range >= 1461:
            ax.xaxis.set_major_locator(mdates.YearLocator())
            date_format = date_format or '%Y'
            ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
            ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 7]))
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        elif date_range >= 366:
            ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
            date_format = date_format or '%Y/%m'
            ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
            ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
            date_format = date_format or '%Y/%m'
            ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
            ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))

    def setYticks(self, ax=None):
        if not ax:
            ax = self.ax

        y_min, y_max = ax.get_ylim()
        y_range = y_max - y_min

        ideal_intervals = (list(range(1, 10, 1))
                           + list(range(10, 100, 10))
                           + list(range(100, 1000, 100))
                           + list(range(1000, 10000, 1000))
                           + list(range(10000, 100000, 10000)))

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
            ax.set_xlim(min_date - timedelta(days=padding),
                        max_date + timedelta(days=padding))
        else:
            start_of_year = mdates.num2date(mdates.datestr2num(f'{min_date.year}-01-01'))
            end_of_year = mdates.num2date(mdates.datestr2num(f'{max_date.year+1}-01-01'))
            ax.set_xlim(start_of_year, end_of_year)

    def updateYlim(self, *, ax=None, y_data):
        if not ax:
            ax = self.ax

        data_min = np.nanmin(y_data)
        data_max = np.nanmax(y_data)

        current_ylim = ax.dataLim.intervaly
        updated_ylim = (min(current_ylim[0], data_min), max(current_ylim[1], data_max))
        ax.set_ylim(updated_ylim)

    def setYlims(self, ax=None, parms={}):
        if not ax:
            ax = self.ax

        # get min/max from data
        # if ax == self.ax:
        #     y_min = np.nanmin(self.plot_values)
        #     y_max = np.nanmax(self.plot_values)
        # elif ax == self.ax_residuals:
        #     y_max = np.nanmax(np.abs(self.residuals_values))
        #     y_min = -y_max

        # get min/max from axis
        y_min, y_max = ax.get_ylim()
        if self.plot_y_axis != "from_data":
            y_max = np.abs([y_min, y_max]).max()
            y_min = -y_max

        ax.set_ylim(y_min, y_max)

        if self.plot_y_axis == "adaptive":
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

        ymin = parms['ymin']
        ymax = parms['ymax']
        ax.set_ylim([ymin, ymax])  # TODO: check if works with ymax or ymin=None

    def setAxisStyle(self, ax=None, parms={}):
        if not ax:
            ax = self.ax

        background_color = parms['background color']
        ax.set_facecolor(background_color)

    def setFigureStyle(self, parms={}):
        background_color = parms['background color']
        self.ui.figure.patch.set_facecolor(background_color)

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

    def _dateStrings(self):
        date_strings = []
        for d in self.dates:
            date_strings.append(d.strftime('%Y-%m-%d'))
        return date_strings

    def exportAscii(self, filename=None):
        if filename is None:
            return
        if self.dates is None or self.plot_values is None:
            return

        data_to_save = np.column_stack((self._dateStrings(), self.plot_values))

        coords = self.coords
        ref_coords = self.ref_coords

        separator = "\n*********************************************************************************************\n"
        header_lines = [separator]
        header_lines.append(f"InSAR Explorer (v{__version__}) - Time Series Export\n")
        header_lines.append("This file contains a time series produced with InSAR Explorer. InSAR Explorer is a free "
                            "QGIS \nplugin for interactive visualization and analysis of InSAR time-series. "
                            "Visit the project website \nfor installation, documentation, license, and examples: "
                            "https://luhipi.github.io/insar-explorer\n"
                            "If you use InSAR Explorer, please cite the paper: "
                            "https://doi.org/10.1109/IGARSS55030.2025.11313961")
        header_lines.append(separator)

        # we either have point or polygons.
        coords_type = "polygon" if hasattr(coords, "geom") else "point"
        ref_coords_type = "polygon" if hasattr(ref_coords, "geom") else "point"
        wgs84 = "CRS=EPSG:4326"

        header_lines.append("Layer CRS\n")
        header_lines.append(f"Time series {coords_type}:")
        header_lines.append(f"{coords.crs_str() if coords else 'None'}")
        header_lines.append(f"{coords.as_wkt() if coords else 'None'}\n")
        header_lines.append(f"Reference {ref_coords_type}:")
        header_lines.append(f"{ref_coords.crs_str() if ref_coords else 'None'}")
        header_lines.append(f"{ref_coords.as_wkt() if ref_coords else 'None'}")

        header_lines.append(separator)
        header_lines.append("WGS84 Lon/Lat\n")
        header_lines.append(f"Time series {coords_type}:")
        header_lines.append(f"{wgs84 if coords else 'None'}")
        header_lines.append(f"{coords.as_wkt_wgs84() if coords else 'None'}\n")
        header_lines.append(f"Reference {ref_coords_type}:")
        header_lines.append(f"{wgs84 if ref_coords else 'None'}")
        header_lines.append(f"{ref_coords.as_wkt_wgs84() if ref_coords else 'None'}")
        header_lines.append(separator)

        header_lines.append("Time series data\n")
        header_lines.append("date, ts_value")

        header = "\n".join(header_lines)
        np.savetxt(filename, data_to_save, fmt="%s", delimiter=",", header=header, comments="# ")

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

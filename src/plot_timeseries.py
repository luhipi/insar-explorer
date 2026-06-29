import os
import sys
from datetime import datetime, timedelta

import numpy as np
from ..external import pyqtgraph as pg
from ..external.pyqtgraph import exporters
from qgis.PyQt.QtGui import QColor, QFont

from .model_fitting import FittingModels
from ..external.setting_manager_ui.json_settings import JsonSettings

sys.path.insert(0, os.path.abspath('../..'))
try:
    from insar_explorer import __version__
except ImportError:
    __version__ = "xx.xx.xx"


class FormattedDateAxisItem(pg.DateAxisItem):
    """Date axis that honors the user-configured strftime label format."""

    def __init__(self, *args, date_format=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_format = date_format

    def tickStrings(self, values, scale, spacing):
        if not self.date_format:
            return super().tickStrings(values, scale, spacing)

        labels = []
        for value in values:
            try:
                labels.append(datetime.fromtimestamp(value).strftime(self.date_format))
            except (OverflowError, OSError, ValueError, TypeError):
                labels.append("")
        return labels


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
        self._y_data_ranges = {}
        self._last_replica_y_data = []

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
            self._clearPlotWidget()
        self._draw()
        self.dates = None
        self.ts_values = 0
        self.ref_values = 0
        self.coords = None
        self.ref_coords = None
        self.plot_list = []
        self.plot_data_list = []
        self.plot_residuals_list = []

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
            self.plot_list = []
            self.plot_data_list = []
            self.plot_residuals_list = []

            if self.plot_residuals_flag:
                if self.ax is not None and self.ax_residuals is not None:
                    self._clearPlotItems()
                else:
                    self._clearPlotWidget()
                    self.ax = self._addPlot(row=0)
                    self.ax_residuals = self._addPlot(row=1)
                    self.ax_residuals.setXLink(self.ax)
                return

            if self.ax is not None and self.ax_residuals is None:
                self._clearPlotItems()
            else:
                self._clearPlotWidget()
                self.ax = self._addPlot(row=0)
                self.ax_residuals = None
            return

        if self.plot_residuals_flag:
            if self.ax is None or self.ax_residuals is None:
                self._clearPlotWidget()
                self.ax = self._addPlot(row=0)
                self.ax_residuals = self._addPlot(row=1)
                self.ax_residuals.setXLink(self.ax)
        else:
            if self.ax is None or self.ax_residuals is not None:
                self._clearPlotWidget()
                self.ax = self._addPlot(row=0)
                self.ax_residuals = None

    def plotTs(self, *, dates=None, ts_values=None, ref_values=None, plot_multiple=True, coords=None, ref_coords=None,
               update=False):
        # update: flag incicating if the plot should be updated or a new one created

        plot_dict = {}
        main_y_data = []
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
        x = self._datesToX(self.dates)

        plot_dict['plot_multiple_fill'] = []
        if plot_multiple and self.min_plot_values is not None:
            lower_bound = self.min_plot_values
            upper_bound = self.max_plot_values
            series_fill_color = parms['series fill color']
            series_fill_alpha = parms['series fill alpha']
            lower_line = pg.PlotDataItem(x, lower_bound, pen=None)
            upper_line = pg.PlotDataItem(x, upper_bound, pen=None)
            fill = pg.FillBetweenItem(
                lower_line,
                upper_line,
                brush=self._brush(series_fill_color, series_fill_alpha)
            )
            self.ax.addItem(lower_line)
            self.ax.addItem(upper_line)
            self.ax.addItem(fill)
            plot_dict['plot_multiple_fill'] = [lower_line, upper_line, fill]
            main_y_data.extend([lower_bound, upper_bound])

        plot_multiple_lines = []

        if self.plot_multiple_values is not None:
            series_line_style = parms['series line style']
            series_line_color = parms['series line color']
            series_line_alpha = parms['series line alpha']
            series_line_width = parms['series line width']
            for i in range(self.plot_multiple_values.shape[1]):
                item = self.ax.plot(
                    x,
                    self.plot_multiple_values[:, i],
                    pen=self._pen(series_line_color, series_line_width, series_line_alpha, series_line_style)
                )
                plot_multiple_lines.append(item)
                main_y_data.append(self.plot_multiple_values[:, i])
        plot_dict['plot_multiple_lines'] = plot_multiple_lines

        if marker_size > 0:
            plot = pg.ScatterPlotItem(x=x, y=self.plot_values, symbol=self._symbol(marker),
                                      size=marker_size,
                                      pen=self._pen(edge_color, 0.2, marker_alpha),
                                      brush=self._brush(marker_color, marker_alpha))
            self.ax.addItem(plot)
        else:
            plot = None
        plot_dict['scatter'] = plot

        main_y_data.append(self.plot_values)

        if line_style != '':
            plot_line = self.ax.plot(
                x,
                self.plot_values,
                pen=self._pen(line_color, line_width, line_alpha, line_style))
        else:
            plot_line = None
        plot_dict['line'] = plot_line

        if self.replicate_flag:
            replicate_up_list, replicate_dn_list = self.plotReplicas()
        else:
            replicate_up_list, replicate_dn_list = [None], [None]
        plot_dict['replicate_up'] = replicate_up_list
        plot_dict['replicate_dn'] = replicate_dn_list

        # update ylim for hold on
        main_y_data.extend([item['y'] for item in self._last_replica_y_data])
        self._last_replica_y_data = []
        plot_dict['main_y_data'] = main_y_data
        self.updateYlim(ax=self.ax, y_data=main_y_data)

        self.decoratePlot(parms=parms)
        fit_plot_list = self.fitModel()
        plot_dict['fit_plot_list'] = fit_plot_list

        parms_figure = self.parms['figure']
        self.decorateFigure(parms=parms_figure)

        self.plot_data_list.append(plot_data_dict)
        self.plot_list.append(plot_dict)
        self._draw()

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
                plot_dict = self.plot_list.pop()
                for key in ('scatter', 'line', 'fit_plot_list'):
                    self._removeItem(self.ax, plot_dict.get(key, None))
                for key in ('plot_multiple_fill', 'plot_multiple_lines', 'replicate_up', 'replicate_dn'):
                    for item in plot_dict.get(key, []) or []:
                        self._removeItem(self.ax, item)

                if self.plot_residuals_list:
                    res_plots = self.plot_residuals_list.pop()
                    self._removeItem(self.ax_residuals, res_plots.get('residual_scatter', None))
                    self._removeItem(self.ax_residuals, res_plots.get('residual_line', None))

                self.plot_data_list.pop()

        self._rebuildYDataRanges()
        self._draw()
        return True

    def plotReplicas(self):
        parms = self.parms['time series plot']
        x = self._datesToX(self.dates)
        marker_color_1 = parms['replica color 1']  # replica up
        marker_color_2 = parms['replica color 2']  # replica down
        marker_alpha = parms['replica alpha']
        marker_size_replica = parms['replica marker size']
        marker_replica = parms['replica marker']
        number_of_up_replicas = parms['number of up replicas']
        number_of_down_replicas = parms['number of down replicas']
        self._last_replica_y_data = []

        # plot multiple replicas
        replicate_up_list = []
        for i in range(number_of_up_replicas):
            replicate_value = self.replicate_value * (i + 1)

            if i % 2 == 0:
                marker_replica_color = marker_color_1
            else:
                marker_replica_color = marker_color_2

            replicate_up = pg.ScatterPlotItem(
                x=x,
                y=self.plot_values + replicate_value,
                symbol=self._symbol(marker_replica),
                size=marker_size_replica,
                pen=None,
                brush=self._brush(marker_replica_color, marker_alpha)
            )
            self.ax.addItem(replicate_up)
            replicate_up_list.append(replicate_up)
            self._last_replica_y_data.append({'y': self.plot_values + replicate_value})

        replicate_dn_list = []
        for i in range(number_of_down_replicas):
            replicate_value = self.replicate_value * (i + 1)

            if i % 2 == 0:
                marker_replica_color = marker_color_2
            else:
                marker_replica_color = marker_color_1

            replicate_dn = pg.ScatterPlotItem(x=x, y=self.plot_values - replicate_value,
                                              symbol=self._symbol(marker_replica), size=marker_size_replica,
                                              pen=None,
                                              brush=self._brush(marker_replica_color, marker_alpha))
            self.ax.addItem(replicate_dn)
            replicate_dn_list.append(replicate_dn)
            self._last_replica_y_data.append({'y': self.plot_values - replicate_value})

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
            fit_plot = self.ax.plot(
                self._datesToX(model_x),
                model_y,
                pen=self._pen(fit_line_color, 1, 1.0, fit_line_type)
            )
            self.residuals_values = self.plot_values - model_values
            self.plotResiduals()
            self._draw()

        return fit_plot

    def plotResiduals(self):
        plot_dict = {'residual_scatter': None, 'residual_line': None}
        if self.plot_residuals_flag and self.ax_residuals is not None:
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

            x = self._datesToX(self.dates)
            marker_size = marker_size or 0
            if marker_size > 0:
                plot_residual = pg.ScatterPlotItem(
                    x=x,
                    y=self.residuals_values,
                    symbol=self._symbol(marker),
                    size=marker_size,
                    pen=self._pen(edge_color, 0.2, marker_alpha),
                    brush=self._brush(marker_color, marker_alpha)
                )
                self.ax_residuals.addItem(plot_residual)
                plot_dict['residual_scatter'] = plot_residual
            if line_style:
                plot_residual_line = self.ax_residuals.plot(
                    x,
                    self.residuals_values,
                    pen=self._pen(line_color, line_width, line_alpha, line_style)
                )
                plot_dict['residual_line'] = plot_residual_line
            plot_dict['residual_y_data'] = [self.residuals_values]
            self.updateYlim(ax=self.ax_residuals, y_data=plot_dict['residual_y_data'])
            self.decoratePlot(ax=self.ax_residuals, parms=parms)
            self._draw()

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
        self.setGrid(ax=ax, parms=parms)
        self.setLabels(ax=ax, parms=parms)
        self.setAxisStyle(ax=ax, parms=parms)

    def setFontSize(self, ax=None, parms={}):
        if not ax:
            ax = self.ax
        font_size = parms['font size']
        font = QFont()
        font.setPointSize(int(font_size))
        for axis_name in ('left', 'bottom'):
            ax.getAxis(axis_name).setTickFont(font)

    def setGrid(self, ax=None, parms={}):
        if not ax:
            ax = self.ax
        grid_type = parms['grid']
        ax.showGrid(x=grid_type in ('vertical', 'both'), y=grid_type in ('horizontal', 'both'), alpha=0.25)

    def setLabels(self, ax=None, parms={}):
        if not ax:
            ax = self.ax

        font_size = f"{int(parms['font size'])}pt"
        if parms['title'] != "":
            ax.setTitle(parms['title'], size=font_size)
        if parms['xlabel'] != "":
            ax.setLabel('bottom', parms['xlabel'], **{'font-size': font_size})
        if parms['ylabel'] != "":
            ax.setLabel('left', parms['ylabel'], **{'font-size': font_size})


    def setXticks(self, ax=None, parms={}):
        if not ax:
            ax = self.ax
        self._applyDateFormat(ax=ax, parms=parms)


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
            x_min = self._dateToX(min_date - timedelta(days=padding))
            x_max = self._dateToX(max_date + timedelta(days=padding))
        else:
            x_min = self._dateToX(datetime(min_date.year, 1, 1))
            x_max = self._dateToX(datetime(max_date.year + 1, 1, 1))
        ax.setXRange(x_min, x_max, padding=0)

    def updateYlim(self, *, ax=None, y_data):
        if not ax:
            ax = self.ax
        data_range = self._finiteRange(y_data)
        if data_range is None:
            return

        key = id(ax)
        current = self._y_data_ranges.get(key)
        if current is None:
            y_min, y_max = data_range
        else:
            y_min = min(current[0], data_range[0])
            y_max = max(current[1], data_range[1])
        self._y_data_ranges[key] = (y_min, y_max)
        if y_min == y_max:
            y_min -= 1
            y_max += 1
        ax.setYRange(y_min, y_max, padding=0.05)

    def setYlims(self, ax=None, parms={}):
        if not ax:
            ax = self.ax

        # get min/max from axis
        y_min, y_max = self._y_data_ranges.get(id(ax), ax.viewRange()[1])
        if self.plot_y_axis != "from_data":
            y_max = np.abs([y_min, y_max]).max()
            y_min = -y_max

        if self.plot_y_axis == "adaptive":
            y_range = y_max - y_min
            y_min_rounded = -5
            y_max_rounded = 5
            for i in [10000, 1000, 100, 10]:
                if y_range >= i:
                    y_min_rounded = np.floor(y_min / i) * i
                    y_max_rounded = np.ceil(y_max / i) * i
                    break

            y_min = np.min([y_min_rounded, -5])
            y_max = np.max([y_max_rounded, 5])

        ymin = parms['ymin'] if parms['ymin'] is not None else y_min
        ymax = parms['ymax'] if parms['ymax'] is not None else y_max
        if ymin == ymax:
            ymin -= 1
            ymax += 1
        ax.setYRange(ymin, ymax, padding=0.05)

    def setAxisStyle(self, ax=None, parms={}):
        if not ax:
            ax = self.ax
        background_color = self._color(parms['background color'])
        ax.getViewBox().setBackgroundColor(background_color)
        self._applyDateFormat(ax=ax, parms=parms)

    def setFigureStyle(self, parms={}):
        background_color = self._color(parms['background color'])
        self.ui.plot_widget.setBackground(background_color)

    def savePlotAsImage(self, filename=None):
        parms = self.parms["export"]
        dpi = int(parms["dpi"])
        pad = parms["pad"]
        fig_size_export = (12, 6) if self.plot_residuals_flag else (12, 3)
        fig_size = self.ui.figure.get_size_inches()
        if filename:
            exporter = exporters.ImageExporter(self.ui.plot_widget.scene())
            exporter.parameters()['width'] = 2400
            exporter.export(filename)

    def _addPlot(self, row=0):
        axis = FormattedDateAxisItem(orientation='bottom', date_format=self.parms['time series plot'].get('date format'))
        plot_item = self.ui.plot_widget.addPlot(row=row, col=0, axisItems={'bottom': axis})
        self._stylePlotFrame(plot_item)
        plot_item.showButtons()
        self.ui.plot_widget.plot_items.append(plot_item)
        return plot_item

    def _stylePlotFrame(self, plot_item):
        plot_item.showAxis('top')
        plot_item.showAxis('right')
        for name in ('left', 'bottom', 'top', 'right'):
            axis = plot_item.getAxis(name)
            axis.setPen(pg.mkPen('k', width=1))
            axis.setTextPen(pg.mkPen('k'))
        for name in ('top', 'right'):
            axis = plot_item.getAxis(name)
            axis.setStyle(showValues=False)
            axis.setTicks([])

    def _clearPlotWidget(self):
        self.ui.plot_widget.clear()
        self.ui.plot_widget.plot_items = []
        self.ax = None
        self.ax_residuals = None
        self._y_data_ranges = {}
        self._last_replica_y_data = []

    def _clearPlotItems(self):
        for plot_item in getattr(self.ui.plot_widget, 'plot_items', []):
            if plot_item is not None:
                plot_item.clear()
                plot_item.setTitle('')
                plot_item.setLabel('bottom', '')
                plot_item.setLabel('left', '')
        self._y_data_ranges = {}

    def _draw(self):
        self.ui.plot_widget.update()

    def _removeItem(self, ax, item):
        if ax is not None and item is not None:
            try:
                ax.removeItem(item)
            except (ValueError, RuntimeError):
                pass

    def _finiteRange(self, y_data):
        arrays = y_data if isinstance(y_data, (list, tuple)) else [y_data]
        finite_values = []
        for values in arrays:
            if values is None:
                continue
            array = np.asarray(values, dtype=float).ravel()
            finite = array[np.isfinite(array)]
            if finite.size:
                finite_values.append(finite)
        if not finite_values:
            return None
        merged = np.concatenate(finite_values)
        return float(np.nanmin(merged)), float(np.nanmax(merged))

    def _rebuildYDataRanges(self):
        self._y_data_ranges = {}
        for plot_dict in self.plot_list:
            self.updateYlim(ax=self.ax, y_data=plot_dict.get('main_y_data', []))
        if self.ax_residuals is not None:
            for res_dict in self.plot_residuals_list:
                self.updateYlim(ax=self.ax_residuals, y_data=res_dict.get('residual_y_data', []))

    def _applyDateFormat(self, ax=None, parms={}):
        if ax is None:
            ax = self.ax
        axis = ax.getAxis('bottom')
        if isinstance(axis, FormattedDateAxisItem):
            axis.date_format = parms.get('date format')

    def _dateToX(self, value):
        if isinstance(value, np.datetime64):
            value = value.astype('datetime64[ms]').astype(datetime)
        return value.timestamp()

    def _datesToX(self, values):
        return np.array([self._dateToX(value) for value in values], dtype=float)

    def _symbol(self, marker):
        return {
            '.': 'o', ',': 'o', 'o': 'o', 's': 's', '^': 't1', 'v': 't', '<': 't3', '>': 't2',
            '+': '+', 'x': 'x', 'd': 'd', 'D': 'd', '*': 'star', 'p': 'p', 'h': 'h'
        }.get(marker, 'o')

    def _color(self, color, alpha=1.0):
        if color is None:
            color = 'black'
        if isinstance(color, np.ndarray):
            color = color.tolist()
        if isinstance(color, (list, tuple)):
            values = [float(c) for c in color]
            if max(values) <= 1.0:
                values = [int(c * 255) for c in values]
            if len(values) == 3:
                values.append(int(alpha * 255))
            return QColor(*values)
        qcolor = QColor(color)
        qcolor.setAlphaF(float(alpha))
        return qcolor

    def _pen(self, color=None, width=1, alpha=1.0, line_style='-'):
        if color is None:
            color = 'black'
        pen = pg.mkPen(self._color(color, alpha), width=width or 1)
        if line_style in ('--', ':', '-.'):
            from qgis.PyQt.QtCore import Qt
            styles = {'--': Qt.DashLine, ':': Qt.DotLine, '-.': Qt.DashDotLine}
            pen.setStyle(styles[line_style])
        return pen

    def _brush(self, color=None, alpha=1.0):
        return pg.mkBrush(self._color(color, alpha))

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

import numpy as np
import matplotlib.dates as mdates
import matplotlib.ticker as ticker


class PlotTs():

    def __init__(self, ui):
        self.ui = ui
        self.ax = None
        self.date_values = None
        self.dates = []
        self.ts_values = []
        self.marker = 'o'

    def plotTs(self, date_values, marker='o'):
        self.ui.figure.clear()
        self.ax = self.ui.figure.add_subplot(111)
        self.dates = date_values[:, 0]
        self.ts_values = date_values[:, 1]
        self.ax.plot(self.dates, self.ts_values, marker)
        self.setXticks()
        self.setYticks()
        self.setGrid(True)
        self.setYlims()
        self.ui.canvas.draw()

    def setGrid(self, status):
        self.ax.grid(status)

    def setXticks(self):
        min_date = np.min(self.dates)
        max_date = np.max(self.dates)
        date_range = (max_date - min_date).days

        if date_range >= 1461:
            self.ax.xaxis.set_major_locator(mdates.YearLocator())
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            self.ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 7]))
            self.ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        elif date_range >= 730:
            self.ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
            self.ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
            self.ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        else:
            self.ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
            self.ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))
            self.ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))

    def setYticks(self):
        self.ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
        self.ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
        self.ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:.0f}'))

    def setYlims(self):
        y_min = np.min(self.ts_values)
        y_max = np.max(self.ts_values)
        y_min_rounded = np.floor(y_min / 10) * 10
        y_max_rounded = np.ceil(y_max / 10) * 10
        self.ax.set_ylim(y_min_rounded, y_max_rounded)


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

import numpy as np

# def plotTs(ui):
#     ui.figure.clear()
#     ax = ui.figure.add_subplot(111)
#     ax.plot(np.arange(10), np.random.random(10))
#     ui.canvas.draw()


import plotly.graph_objs as go
import plotly.io as pio


def plotTs(ui):
    """
    Plot time series
    """
    fig = go.Figure(data=[go.Scatter(x=list(range(100)), y=np.random.random(100))])
    fig.update_layout(margin=dict(l=0.1, r=0.1, t=0.1, b=0.1))
    html = pio.to_html(fig, full_html=False)
    ui.web_view.setHtml(html)



def applyPyqtgraphCompatPatches() -> None:
    """
    Apply runtime compatibility patches for the bundled pyqtgraph package.

    QGIS 4 (Qt6) expects PlotDataItem to provide a paint() method during SVG
    export. Older bundled versions of pyqtgraph do not implement this method,
    resulting in warnings during export. This patch adds a no-op implementation
    only when the method is absent.

    Safe to call multiple times.
    """
    from ..external.pyqtgraph.graphicsItems.PlotDataItem import PlotDataItem

    if "paint" not in PlotDataItem.__dict__:
        def paint(self, *args):
            pass

        PlotDataItem.paint = paint

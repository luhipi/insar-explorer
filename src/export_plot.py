import os
from contextlib import contextmanager

from ..external.pyqtgraph import exporters
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QApplication


class TimeSeriesPlotExporter:
    """Export the existing time-series plot without rebuilding it."""

    BASE_DPI = 96.0
    DEFAULT_DPI = 300
    DEFAULT_ASPECT_RATIO = 4.0

    def __init__(self, plotter):
        self.plotter = plotter

    def export(self, filename=None):
        if filename is None:
            return
        if not self.plotter.plot_data_list:
            return

        plot_widget = self.plotter.ui.plot_widget
        export_item = getattr(plot_widget, 'ci', None) or plot_widget.scene()
        if export_item is None:
            return

        dpi, aspect_ratio = self._exportSettings()
        logical_width, logical_height = self._logicalExportSize(plot_widget, aspect_ratio)
        export_width = max(1, int(round(logical_width * dpi / self.BASE_DPI)))
        export_height = max(1, int(round(logical_height * dpi / self.BASE_DPI)))
        suffix = os.path.splitext(filename)[1].lower()

        with self._temporaryPlotSize(plot_widget, logical_width, logical_height):
            if suffix == '.svg':
                exporters.SVGExporter(export_item).export(filename)
                return

            if suffix == '.pdf':
                # Pyqtgraph does not provide reliable vector PDF export for this plot.
                # Use SVG for vector output.
                return

            exporter = exporters.ImageExporter(export_item)
            self._setExporterParameter(exporter, 'width', export_width)
            self._setExporterParameter(exporter, 'height', export_height)
            exporter.export(filename)

    def _exportSettings(self):
        export_parms = self.plotter.parms.get('export', {})
        try:
            dpi = int(export_parms.get('dpi') or self.DEFAULT_DPI)
        except (TypeError, ValueError):
            dpi = self.DEFAULT_DPI

        try:
            aspect_ratio = float(export_parms.get('aspect ratio') or self.DEFAULT_ASPECT_RATIO)
        except (TypeError, ValueError):
            aspect_ratio = self.DEFAULT_ASPECT_RATIO
        if aspect_ratio <= 0:
            aspect_ratio = self.DEFAULT_ASPECT_RATIO

        return dpi, aspect_ratio

    def _logicalExportSize(self, plot_widget, aspect_ratio):
        number_of_plots = 2 if self.plotter.plot_residuals_flag else 1
        logical_width = max(1, int(round(plot_widget.width() or 1200)))
        logical_height = max(1, int(round(number_of_plots * logical_width / aspect_ratio)))
        return logical_width, logical_height

    @contextmanager
    def _temporaryPlotSize(self, plot_widget, width, height):
        old_size = plot_widget.size()
        old_min_size = plot_widget.minimumSize()
        old_max_size = plot_widget.maximumSize()
        old_updates_enabled = plot_widget.updatesEnabled()

        try:
            plot_widget.setUpdatesEnabled(False)
            plot_widget.setFixedSize(QSize(width, height))
            plot_widget.resize(width, height)
            self._resizeCentralItem(plot_widget, width, height)
            plot_widget.updateGeometry()
            plot_widget.update()
            QApplication.processEvents()
            yield
        finally:
            plot_widget.setMinimumSize(old_min_size)
            plot_widget.setMaximumSize(old_max_size)
            plot_widget.resize(old_size)
            self._resizeCentralItem(plot_widget, old_size.width(), old_size.height())
            plot_widget.setUpdatesEnabled(old_updates_enabled)
            plot_widget.updateGeometry()
            plot_widget.update()
            QApplication.processEvents()

    def _resizeCentralItem(self, plot_widget, width, height):
        central_item = getattr(plot_widget, 'ci', None)
        if central_item is None:
            return
        try:
            central_item.resize(width, height)
        except AttributeError:
            pass
        scene = plot_widget.scene()
        if scene is not None:
            try:
                scene.setSceneRect(0, 0, width, height)
            except TypeError:
                pass

    def _setExporterParameter(self, exporter, name, value):
        """Set a pyqtgraph exporter parameter across supported API variants."""
        parameters = exporter.parameters()
        try:
            parameters[name] = int(value)
        except Exception:
            pass
        try:
            parameters.param(name).setValue(int(value))
        except Exception:
            pass

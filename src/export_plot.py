import os
import re
from contextlib import contextmanager

from ..external.pyqtgraph import exporters
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QFont, QImage, QPainter
from qgis.PyQt.QtWidgets import QApplication

from .qt_compat import ALIGN_RIGHT_VCENTER


class TimeSeriesPlotExporter:
    """Export the existing time-series plot without rebuilding it."""

    BASE_DPI = 96.0
    DEFAULT_DPI = 300
    DEFAULT_ASPECT_RATIO = 4.0
    DEFAULT_CREDIT = 'Powered by InSAR Explorer'
    DEFAULT_CREDIT_MARGIN = 8
    DEFAULT_CREDIT_FONT_SIZE = 9
    DEFAULT_CREDIT_FOOTER_HEIGHT = 22

    def __init__(self, plotter):
        self.plotter = plotter

    def export(self, filename=None):
        if filename is None:
            return
        if not self.plotter.series_history:
            return

        plot_widget = self.plotter.ui.plot_widget
        export_item = getattr(plot_widget, 'ci', None) or plot_widget.scene()
        if export_item is None:
            return

        dpi, aspect_ratio, credit = self._exportSettings()
        logical_width, logical_height = self._logicalExportSize(plot_widget, aspect_ratio)
        export_width = max(1, int(round(logical_width * dpi / self.BASE_DPI)))
        export_height = max(1, int(round(logical_height * dpi / self.BASE_DPI)))
        suffix = os.path.splitext(filename)[1].lower()

        with self._temporaryPlotSize(plot_widget, logical_width, logical_height):
            if suffix == '.svg':
                exporters.SVGExporter(export_item).export(filename)
                self._addCreditToSvg(filename, logical_width, logical_height, credit)
                return

            if suffix == '.pdf':
                # Pyqtgraph does not provide reliable vector PDF export for this plot.
                # Use SVG for vector output.
                return

            exporter = exporters.ImageExporter(export_item)
            self._setExporterParameter(exporter, 'width', export_width)
            self._setExporterParameter(exporter, 'height', export_height)
            exporter.export(filename)
            self._addCreditToRaster(filename, dpi, credit)

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

        credit = export_parms.get('credit')
        if credit is None:
            credit = self.DEFAULT_CREDIT
        credit = str(credit)

        return dpi, aspect_ratio, credit

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
            self._flushPlotGeometry(plot_widget)
            yield
        finally:
            plot_widget.setMinimumSize(old_min_size)
            plot_widget.setMaximumSize(old_max_size)
            plot_widget.resize(old_size)
            self._resizeCentralItem(plot_widget, old_size.width(), old_size.height())
            self._flushPlotGeometry(plot_widget)
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

    def _flushPlotGeometry(self, plot_widget):
        """Force pyqtgraph layout and ViewBox transforms to match the export size."""
        plot_widget.updateGeometry()
        plot_widget.update()
        QApplication.processEvents()

        central_item = getattr(plot_widget, 'ci', None)
        layout = getattr(central_item, 'layout', None)
        if layout is not None:
            try:
                layout.activate()
            except AttributeError:
                pass

        for plot_item in getattr(plot_widget, 'plot_items', []):
            try:
                view_box = plot_item.getViewBox()
            except AttributeError:
                continue
            if hasattr(view_box, '_matrixNeedsUpdate'):
                view_box._matrixNeedsUpdate = True
            try:
                view_box.updateMatrix()
            except AttributeError:
                pass

        QApplication.processEvents()

    def _addCreditToRaster(self, filename, dpi, credit):
        if not credit:
            return

        suffix = os.path.splitext(filename)[1].lower()
        if suffix not in ('.png', '.jpg'):
            return

        plot_image = QImage(filename)
        if plot_image.isNull():
            return

        scale = max(1.0, float(dpi) / self.BASE_DPI)
        margin = int(round(self.DEFAULT_CREDIT_MARGIN * scale))
        footer_height = int(round(self.DEFAULT_CREDIT_FOOTER_HEIGHT * scale))

        image = QImage(
            plot_image.width(),
            plot_image.height() + footer_height,
            plot_image.format()
        )
        image.fill(self._figureBackgroundColor())

        font = QFont()
        font.setPixelSize(max(1, int(round(self.DEFAULT_CREDIT_FONT_SIZE * scale))))

        painter = QPainter(image)
        try:
            painter.drawImage(0, 0, plot_image)
            painter.setFont(font)
            painter.setPen(QColor(110, 110, 110))
            painter.drawText(
                margin,
                plot_image.height(),
                image.width() - 2 * margin,
                footer_height,
                ALIGN_RIGHT_VCENTER,
                credit
            )
        finally:
            painter.end()
        image.save(filename)

    def _addCreditToSvg(self, filename, width, height, credit):
        if not credit:
            return

        try:
            svg_text = open(filename, 'r', encoding='utf-8').read()
        except OSError:
            return

        margin = self.DEFAULT_CREDIT_MARGIN
        font_size = self.DEFAULT_CREDIT_FONT_SIZE
        footer_height = self.DEFAULT_CREDIT_FOOTER_HEIGHT
        total_height = height + footer_height

        svg_text = self._resizeSvgCanvas(svg_text, width, total_height)
        escaped_credit = self._escapeSvgText(credit)
        background = self._figureBackgroundColor().name()
        footer = (
            f'\n<rect id="insar-explorer-export-credit-background" '
            f'x="0" y="{height:.3f}" width="{width:.3f}" height="{footer_height:.3f}" '
            f'fill="{background}"/>\n'
            f'<text id="insar-explorer-export-credit" '
            f'x="{width - margin:.3f}" y="{height + footer_height / 2.0:.3f}" '
            f'text-anchor="end" dominant-baseline="middle" '
            f'font-family="Arial, Helvetica, sans-serif" '
            f'font-size="{font_size}px" fill="#6e6e6e">'
            f'{escaped_credit}</text>\n'
        )

        insert_at = svg_text.rfind('</svg>')
        if insert_at < 0:
            return
        svg_text = svg_text[:insert_at] + footer + svg_text[insert_at:]
        try:
            open(filename, 'w', encoding='utf-8').write(svg_text)
        except OSError:
            pass

    def _resizeSvgCanvas(self, svg_text, width, height):
        match = re.search(r'<svg\b[^>]*>', svg_text, flags=re.IGNORECASE)
        if match is None:
            return svg_text

        root = match.group(0)

        root = re.sub(
            r'\s+(width|height|viewBox)\s*=\s*("[^"]*"|\'[^\']*\')',
            '',
            root,
            flags=re.IGNORECASE
        )

        root = root[:-1] + (
            f' width="{width:.3f}"'
            f' height="{height:.3f}"'
            f' viewBox="0 0 {width:.3f} {height:.3f}">'
        )

        return svg_text[:match.start()] + root + svg_text[match.end():]

    def _figureBackgroundColor(self):
        color = self.plotter.parms.get('figure', {}).get('background color') or 'white'
        return QColor(color)

    def _escapeSvgText(self, text):
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

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

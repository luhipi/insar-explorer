from functools import wraps
from importlib import import_module


_CLOSE_PATH_COMMANDS = frozenset(('Z', 'z'))
_SVG_COORDINATE_PATCH_MARKER = '_insarExplorerClosePathPatch'


def _protectStandaloneClosePathCommands(node):
    """Give standalone SVG close-path commands temporary coordinates.

    The SVG path parser in the bundled pyqtgraph release assumes that every
    whitespace-delimited path token contains an ``x,y`` coordinate pair. Qt 6
    can emit ``Z`` or ``z`` as a separate token, especially on Windows. A
    temporary zero coordinate lets the original parser transform the path
    without changing the surrounding pyqtgraph implementation.

    :param node: SVG DOM node whose path descendants will be protected.
    :return: Path elements changed by this function.
    :rtype: list
    """
    protected_paths = []
    for path in node.getElementsByTagName('path'):
        path_data = path.getAttribute('d')
        tokens = path_data.split()
        if not any(token in _CLOSE_PATH_COMMANDS for token in tokens):
            continue

        path.setAttribute(
            'd',
            ' '.join(
                f'{token}0,0' if token in _CLOSE_PATH_COMMANDS else token
                for token in tokens
            )
        )
        protected_paths.append(path)

    return protected_paths


def _restoreStandaloneClosePathCommands(paths):
    """Restore close-path commands protected before coordinate correction.

    :param paths: SVG path elements previously protected.
    :type paths: iterable
    """
    for path in paths:
        tokens = path.getAttribute('d').split()
        path.setAttribute(
            'd',
            ' '.join(
                token[0]
                if token and token[0] in _CLOSE_PATH_COMMANDS
                else token
                for token in tokens
            )
        )


def _patchSvgCoordinateCorrection():
    """Patch the bundled SVG exporter for Qt 6 close-path output."""
    package_root = __package__.rsplit('.', 1)[0]
    svg_exporter = import_module(
        f'{package_root}.external.pyqtgraph.exporters.SVGExporter'
    )
    original = svg_exporter.correctCoordinates

    if getattr(original, _SVG_COORDINATE_PATCH_MARKER, False):
        return

    @wraps(original)
    def correctCoordinates(node, defs, item, options):
        protected_paths = _protectStandaloneClosePathCommands(node)
        try:
            return original(node, defs, item, options)
        finally:
            _restoreStandaloneClosePathCommands(protected_paths)

    setattr(correctCoordinates, _SVG_COORDINATE_PATCH_MARKER, True)
    svg_exporter.correctCoordinates = correctCoordinates


def applyPyqtgraphCompatPatches() -> None:
    """
    Apply runtime compatibility patches for the bundled pyqtgraph package.

    QGIS 4 (Qt6) expects PlotDataItem to provide a paint() method during SVG
    export. Older bundled versions of pyqtgraph do not implement this method,
    resulting in warnings during export. This patch adds a no-op implementation
    only when the method is absent.

    Qt 6 on Windows may also emit standalone SVG close-path commands. The
    bundled SVG exporter treats every path token as an x,y pair, causing a
    ValueError. A narrow wrapper protects those commands while the original
    coordinate correction runs and restores them immediately afterwards.

    Safe to call multiple times.
    """
    from ..external.pyqtgraph.graphicsItems.PlotDataItem import PlotDataItem

    if "paint" not in PlotDataItem.__dict__:
        def paint(self, *args):
            pass

        PlotDataItem.paint = paint

    _patchSvgCoordinateCorrection()

import re
from qgis.core import Qgis


def qgisVresion():
    """return the version of QGIS as a tuple of integers
    usage example:
    if qgisVresion() < (3, 0):
        # do something
    else:
        # do something else
    """
    version_str = Qgis.QGIS_VERSION
    numeric_parts = re.findall(r'\d+', version_str)
    return tuple(map(int, numeric_parts))



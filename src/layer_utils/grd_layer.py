import os
import re
from osgeo import gdal
from qgis.core import QgsMapLayer


def checkGrdLayer(layer):
    if layer is None:
        message = '<span style="color:red;">No layer selected: Please select a raster layer.</span>'
        return False, message
    elif not layer.isValid():
        message = '<span style="color:red;">Invalid Layer: Please select a valid raster layer.</span>'
        return False, message
    elif (layer.type() == QgsMapLayer.VectorLayer):
        message = ('<span style="color:red;">This is a vector layers. Please select a raster layer.'
                   '</span>')
        return False, message

    file_path = layer.source()
    dataset = gdal.Open(file_path)

    if dataset is None:
        message = '<span style="color:red;">Invalid Layer: Unable to open the file with GDAL.</span>'
        return False, message

    driver = dataset.GetDriver().ShortName
    if driver in ['netCDF', 'GMT']:  # for GMTSAR and MintPy files converted to grd
        return True, ""
    else:
        message = '<span style="color:red;">Invalid Layer: The file is not a GMT grd file.</span>'
        return False, message


def checkGrdTimeseries(layer):
    """ check layer is a valid vector with velocity """
    message = ""
    status, message = checkGrdLayer(layer)
    if status is False:
        return status, message

    file_path = layer.source()
    directory = os.path.dirname(file_path)
    pattern = re.compile(r'^\d{8}_.*\.grd|timeseries-\d{8}.*\.grd')

    grd_files = [f for f in os.listdir(directory) if pattern.match(f)]

    count = len(grd_files)

    if count > 0:
        status = True
    else:
        message = ('<span style="color:red;">Invalid Layer: Please select a vector or raster layer with valid '
                   'timeseries data.')
        status = False

    return status, message


def getGrdInfo(directory) -> (list, list):
    """
    Get the list of grd time series files and their dates
    """
    pattern = re.compile(r'^\d{8}_.*\.grd|timeseries-\d{8}.*\.grd')

    grd_files = sorted([f for f in os.listdir(directory) if pattern.match(f)])
    if not grd_files:
        return [], []

    # full paths
    grd_file_paths = [os.path.join(directory, f) for f in grd_files]

    date_pattern = re.compile(r'^\d{8}|timeseries-\d{8}')
    band_names = []
    for grd_file in grd_file_paths:
        match = date_pattern.match(os.path.basename(grd_file))
        if match:
            date_str = match.group(0)
            date_str = removeTimeseriesPrefix(date_str)
            band_name = f'D{date_str}'
            band_names.append(band_name)

    if len(grd_file_paths) != len(band_names):
        raise ValueError("Number of .grd files and band names do not match.")

    return grd_file_paths, band_names

def removeTimeseriesPrefix(filename):
    pattern = re.compile(r'^timeseries-')
    return re.sub(pattern, '', filename)
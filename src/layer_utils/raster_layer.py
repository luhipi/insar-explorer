import os
from datetime import datetime
import numpy as np
from osgeo import gdal

from . import gmtsar_layer as gmtsar_layer_utils



def createVrtFromFiles(*, raster_file_paths, band_names=None, out_file="") -> gdal.Dataset:
    """
    Create a VRT file in memory from a list of .grd files and rename each dataset based on its date.
    :param raster_file_paths: List of .grd file paths
    :param band_names: List of band names. Default is None.
    :param out_file: Output file path. Default is an empty string for in-memory vrt file.
    :return: VRT dataset
    """

    vrt_options = gdal.BuildVRTOptions(separate=True)
    vrt_dataset = gdal.BuildVRT(out_file, raster_file_paths, options=vrt_options)

    # Rename bands
    if band_names is None:
        return vrt_dataset

    for i, band_name in enumerate(band_names, start=1):
        band = vrt_dataset.GetRasterBand(i)
        if band is not None:
            band.SetDescription(band_name)

    return vrt_dataset


def getRasterTimeseriesAttributes(layer, point, time_series_data):
    """
    Get the timeseries values of the clicked point from the GMTSAR grd files.
    The grd files should be in the same directory as the layer (typically velocity) file.
    """
    file_path = layer.source()
    directory = os.path.dirname(file_path)

    raster_file_paths, band_names = gmtsar_layer_utils.getGmtsarGrdInfo(directory)
    dataset = createVrtFromFiles(raster_file_paths=raster_file_paths,
                                                    band_names=band_names, out_file="")

    if not dataset:
        return np.array([]), time_series_data

    date_value_list, time_series_data = getVrtTimeseriesAttributes(dataset, point, time_series_data)
    return date_value_list, time_series_data


def getVrtTimeseriesAttributes(vrt_dataset, point, time_series_data, memory_limit=500):
    """
    Get the timeseries values of the clicked point from a vrt file that consists of time series data.
    The vrt file should have description for each band in the format 'DYYYYMMDD'.
    :param vrt_dataset: VRT dataset
    :param point: QgsPointXY
    :param time_series_data: numpy array
    :param memory_limit: int in Mb
    """

    transform = vrt_dataset.GetGeoTransform()
    inv_transform = gdal.InvGeoTransform(transform)

    x, y = point.x(), point.y()
    px, py = gdal.ApplyGeoTransform(inv_transform, x, y)
    px, py = int(px), int(py)

    band = vrt_dataset.GetRasterBand(1)
    x_size = band.XSize
    y_size = band.YSize
    if not (0 <= px < x_size and 0 <= py < y_size):
        return np.array([]), time_series_data

    num_bands = vrt_dataset.RasterCount
    data_type_size = gdal.GetDataTypeSize(band.DataType) // 8  # Size in bytes
    expected_size = x_size * y_size * num_bands * data_type_size

    if expected_size > memory_limit*1024*1024:
        pixel_values = vrt_dataset.ReadAsArray(px, py, 1, 1)
        if pixel_values is None:
            return np.array([]), time_series_data
        pixel_values = pixel_values[:, 0, 0]

    else:  # read full data at once
        if time_series_data is None:
            time_series_data = vrt_dataset.ReadAsArray()
        pixel_values = time_series_data[:, py, px]

    if pixel_values is None:
        return np.array([]), time_series_data

    date_value_list = []
    date_objs = [datetime.strptime(vrt_dataset.GetRasterBand(i).GetDescription()[1:], '%Y%m%d') for i in
                 range(1, vrt_dataset.RasterCount + 1)]

    for date_obj, pixel_value in zip(date_objs, pixel_values):
        if not np.isnan(pixel_value):
            date_value_list.append((date_obj, pixel_value))

    return np.array(date_value_list, dtype=object), time_series_data

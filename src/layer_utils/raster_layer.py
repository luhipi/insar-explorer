from osgeo import gdal


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
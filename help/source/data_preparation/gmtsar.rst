**GMTSAR**
^^^^^^^^^^

  GMTSAR provides time series data in raster `grd` format. This data can be processed in InSAR Explorer using one of two methods:

  **Method 1: Use the grd Files Directly**

      You can directly use the raster `grd` files created by GMTSAR in InSAR Explorer. The expected directory structure for the `grd` files is as follows:

      .. code-block:: none

          -| GMTSAR_output/
            -| vel_*.grd
            -| YYYYMMDD_*.grd
            -| YYYYMMDD_*.grd
            -| ...

      To use this method:
      1. Ensure the `grd` files associated with the time series are located in the same directory as the `vel_*.grd` file.
      2. Open the original `vel_*.grd` file created by GMTSAR in QGIS.
      3. Set the correct Coordinate Reference System (CRS) for the QGIS project (typically `WGS 84`).

      InSAR Explorer will automatically detect the associated time series files and handle them accordingly.

  **Method 2: Convert grd to Vector Format**

      It is possible to convert the time series data from raster `grd` format to vector formats such as shapefile or geopackage.

      **Note**: You should create the shapefile with proper format as described in  :doc:`../data_structure`



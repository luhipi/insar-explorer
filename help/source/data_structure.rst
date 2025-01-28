Data Structure
**************

    The plugin primarily requires a vector file (e.g., a shapefile or geopackage) containing time series data. The file should have the following attributes:

    .. list-table::
       :header-rows: 1

       * - Field Name
         - Description
       * - ``velocity``, ``VEL``, or ``mean_velocity``
         - Or a similar field containing the InSAR velocity data.
       * - ``DYYYYMMDD`` or ``YYYYMMDD`` or ``D_YYYYMMDD``
         - Multiple fields for time series data, where ``YYYYMMDD`` is the date of the data, e.g., ``D20190101``, ``D20190201``, etc.

    For specific time series outputs, like from GMTSAR, InSAR Explorer supports raster format as well.
    Please refer to the relevant section for :doc:`data_preparation/gmtsar` in the documentation for more information.
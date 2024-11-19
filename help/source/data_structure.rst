Data Structure
**************

The plugin requires a vector file (e.g., a shapefile or geopackage) containing time series data. The file should have the following attributes:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``velocity`` or ``VEL``
     - A field containing the InSAR velocity data.
   * - ``DYYYYMMDD``
     - Multiple fields for time series data, where ``YYYYMMDD`` is the date of the data, e.g., ``D20190101``, ``D20190201``, etc.


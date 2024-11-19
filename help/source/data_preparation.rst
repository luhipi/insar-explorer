
Data preparation
****************

The data can be prepared for different software tools as follows:

- **SARvey**

  Use the ``sarvey_export`` script to export the time series data to a shapefile or geopackage file. For example:

  ``$ sarvey_export outputs/p2_coh80_ts.h5 -o outputs/shp/p2_coh80_ts.shp``

- **MintPy or MIaplPy**

  Use the ``save_qgis`` script to export the time series data to a shapefile. For example:

  ``$ mintpy save_qgis timeseries_ERA5_ramp_demErr.h5 -g inputs/geometrygeo.h5``

- **StaMPS**
   to be added.


**Note:** if you are an InSAR software developer interested in incorporating data visualization support within InSAR Explorer, please reach out to us.

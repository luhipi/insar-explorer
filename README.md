![InSAR Explorer](icon.png)

# InSAR Explorer

## Description
InSAR Explorer is a QGIS plugin that allows for dynamic visualization and analysis of InSAR time series data. 
InSAR Explorer supports visualizing outputs of 
[SARvey Open-source research software for InSAR time series analysis](https://github.com/luhipi/sarvey)
as well as outputs from 
[MintPy](https://github.com/insarlab/MintPy) 
and 
[MiaplPy](https://github.com/insarlab/MiaplPy) 
software.

## Installation
### Method 1: Download from QGIS Plugin Repository
1. Open QGIS.
2. Go to `Plugins` > `Manage and Install Plugins…`.
3. In the `All` tab of the Plugin Manager, type `Insar Explorer` in the search bar.
4. Select the `InSAR Explorer` plugin from the list and click `Install Plugin`.

### Method 2: Install the development version from ZIP file
1. Download the plugin Repository as ZIP.
2. Open QGIS.
3. Go to `Plugins` > `Manage and Install Plugins`.
4. Click on the `Install from ZIP` tab.
5. Select the downloaded ZIP file and click `Install Plugin`.
 
## Usage
1. Open a vector layer with InSAR time series data.
2. Click on the plugin icon in the toolbar or go to `Plugins` > `InSAR Explorer`.
3. Click on any point in the map to display the time series data.

## Data Structure

The plugin requires a vector file (e.g., a shapefile or geopackage) containing time series data. The file should have the following attributes:

| Field Name | Description |
|------------|-------------|
| `velocity` or `VEL` | A field containing the InSAR velocity data. |
| `DYYYYMMDD` | Multiple fields for time series data, where `YYYYMMDD` is the date of the data, e.g., `D20190101`, `D20190201`, etc. |


## Sample data
A sample shapefile containing time series data for testing the plugin is available on [Zenodo repository](https://zenodo.org/records/14052814).

## Data preparation
The data can be prepared for different software tools as follows:

| Software | Command                                                                                                                                                                                    |
|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **SARvey** | Use the `sarvey_export` script to export the time series data to a shapefile or geopackage file. For example: <br/>`$ sarvey_export outputs/p2_coh80_ts.h5 -o outputs/shp/p2_coh80_ts.shp` |
| **MintPy or MIaplPy** | Use the `save_qgis` script to export the time series data to a shapefile. For example: <br/>`$ mintpy save_qgis timeseries_ERA5_ramp_demErr.h5 -g inputs/geometrygeo.h5`                   |
| **StaMPS** | to be added.                                                                                                                                                                               |

###### If you are an InSAR software developer interested in incorporating data visualization support within InSAR Explorer, please reach out to us.

## Contributing
1. Fork the repository on GitHub.
2. Create a new branch for your feature or bug fix.
3. Commit your changes and push to your branch.
4. Create a pull request to the main repository.

## License
This plugin is licensed under the GPL-2.0 license. See the `LICENSE` file for more details. 

Authors: [Mahmud Haghighi](https://www.ipi.uni-hannover.de/en/haghighi/),
           [Andreas Piter](https://www.ipi.uni-hannover.de/en/piter/)

## Contact
For any questions or issues, please create an [issue](https://github.com/luhipi/insar_explorer/issues) on the [GitHub repository](https://github.com/luhipi/insar_explorer).

### History

v1.1.0dev
- Change the reference point for the map on the fly.
- Enhance labeling of the map plot

v1.0.0
- Sync colorbar icon with reverse button
- Disable log
- Update documentation for SARscape and MintPy support.
- Add a menubar for selecting data range
- Support MintPy time series data created via save_explorer command
- Removed default ylabe units from time series plot to avoid confusion for data from different sources
- Enhance display of icons to differentiate between checkable and non-checkable buttons
- Add about dialog
- New icon designs for the plugin
- New icon for symbology and add icon for live symbology 
- Add gray to the list of colormaps
- Handle NULL values in time series data
- Add different options to control y-axis limits
- Make field selector editable to improve user experience
- Ignore non-numerical fields in the field selector
- A hold-on button to keep the plot after selecting a new point
- Keep the time series plot when layer changed
- New icon for residual plot button

v0.8.0
- Allow D_YYYYMMDD time series date format
- Add combobox to select field for visualization
- Change Groupbox name: Range to Value
- Add linting to improve code readability, consistency, and maintainability.
- Upgrade to SettingsManagerUI v0.5.0
- Move external libraries to `external` folder.


v0.7.0
- Read settings from a JSON file
- Integrate SettingsManagerUI for managing settings
- Add setting button to the time series tab

v0.6.1
- Fix bug in initial import
- Fix bugs in icon
- Correct link to documentation


v0.6.0
- Add support for EGMS products.
- Add support for GMTSAR grd time series.
- Reset parameters after layer change.


v0.5.0
- Add toolbar to time series plot for zooming, panning, etc.
- Add push buttons for getting map symbology range from data
- Resurface the gui with a new design.
- Check layer validity before plotting.

v0.4.0
- Add save button for time series plot supporting png, jpg, pdf, svg.
- Set Y-axis ticks adaptively based on the data range.
- Enhance the style of the time series plot.
- Add support for MintPy and MiaplPy software.
- Introduce a new website theme.
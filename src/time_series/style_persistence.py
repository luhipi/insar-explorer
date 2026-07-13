"""Persistence helpers for time-series default plot styles."""

from ...external.setting_manager_ui.json_settings import JsonSettings


STYLE_KEYS = (
    "marker",
    "marker color",
    "marker size",
    "line style",
    "line color",
    "line width",
)


def persist_default_time_series_style(config_file, style):
    """Persist a complete series style while preserving unrelated JSON settings."""
    plot_values = style.params.get("time series plot", {})
    settings = JsonSettings(config_file)
    settings_block = settings.load(block_key="timeseries settings")
    plot_settings = settings_block.get("time series plot")
    if not isinstance(plot_settings, dict):
        raise KeyError("Missing timeseries settings/time series plot configuration block")

    for key in STYLE_KEYS:
        if key not in plot_values:
            continue
        entry = plot_settings.get(key)
        if not isinstance(entry, dict):
            raise KeyError(f"Missing time-series plot style setting: {key}")
        entry["value"] = plot_values[key]

    settings.save("timeseries settings", settings_block)

"""Compatibility persistence entry point for time-series default styles."""

from .style_config import TimeSeriesStyleConfig


def persist_default_time_series_style(config_file, style):
    """Persist a complete series style through the plugin-owned config adapter."""
    TimeSeriesStyleConfig(config_file).save_default_style(style)

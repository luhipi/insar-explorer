"""Plugin-owned adapter between config.json and time-series style models."""

from copy import deepcopy

from ...external.setting_manager_ui.json_settings import JsonSettings
from ..models.time_series import TimeSeriesStyle
from .fit_style_controller import FIT_STYLE_KEYS, FitStyle
from .style_schema import (
    FIT_LINE_STYLE_OPTIONS,
    FIT_LINE_WIDTH_DEFAULT,
    FIT_LINE_WIDTH_RANGE,
    LINE_STYLE_OPTIONS,
    LINE_WIDTH_RANGE,
    MARKER_OPTIONS,
    MARKER_SIZE_RANGE,
    PERSISTED_STYLE_KEYS,
    normalize_color,
    normalize_fit_line_style,
    normalize_line_style,
    normalize_marker,
    normalize_number,
)


class TimeSeriesStyleConfig:
    """Translate between the Settings JSON metadata schema and ``TimeSeriesStyle``."""

    BLOCK_KEY = "timeseries settings"
    PLOT_KEY = "time series plot"

    def __init__(self, config_file):
        """Store the configuration path without caching persisted values."""
        self.config_file = config_file

    def load_style_values(self):
        """Load and normalize every persisted series-style value."""
        settings = JsonSettings(self.config_file)
        block = settings.load(block_key=self.BLOCK_KEY)
        plot = block.get(self.PLOT_KEY, {})
        values = {}
        for key in PERSISTED_STYLE_KEYS:
            entry = plot.get(key, {})
            value = entry.get("value", entry.get("default")) if isinstance(entry, dict) else None
            values[key] = self.normalize_property(key, value)
        return values

    def load_default_style(self, base_params=None):
        """Return normalized defaults merged into a defensive parameter copy."""
        params = deepcopy(base_params) if isinstance(base_params, dict) else {}
        params.setdefault(self.PLOT_KEY, {}).update(self.load_style_values())
        return TimeSeriesStyle.fromParams(params)

    def save_default_style(self, style):
        """Persist style values while preserving unrelated settings and metadata."""
        plot_values = style.params.get(self.PLOT_KEY, {})
        settings = JsonSettings(self.config_file)
        block = settings.load(block_key=self.BLOCK_KEY)
        plot = block.get(self.PLOT_KEY)
        if not isinstance(plot, dict):
            raise KeyError("Missing timeseries settings/time series plot configuration block")

        for key in PERSISTED_STYLE_KEYS:
            if key not in plot_values:
                continue
            entry = plot.get(key)
            if not isinstance(entry, dict):
                raise KeyError(f"Missing time-series plot style setting: {key}")
            entry["value"] = self.normalize_property(key, plot_values[key])

        settings.save(self.BLOCK_KEY, block)


    def load_fit_style_values(self):
        """Load and normalize persisted fit-line defaults."""
        settings = JsonSettings(self.config_file)
        block = settings.load(block_key=self.BLOCK_KEY)
        fit = block.get("model fit", {})
        values = {}
        for key in FIT_STYLE_KEYS:
            entry = fit.get(key, {})
            value = entry.get("value", entry.get("default")) if isinstance(entry, dict) else None
            values[key] = self.normalize_fit_property(key, value)
        return values

    def load_default_fit_style(self):
        """Return normalized persisted fit-line defaults."""
        return FitStyle.fromParams({"model fit": self.load_fit_style_values()})

    def save_default_fit_style(self, fit_style):
        """Persist fit-line defaults while preserving settings metadata."""
        values = fit_style.asParams() if isinstance(fit_style, FitStyle) else dict(fit_style)
        settings = JsonSettings(self.config_file)
        block = settings.load(block_key=self.BLOCK_KEY)
        fit = block.get("model fit")
        if not isinstance(fit, dict):
            raise KeyError("Missing timeseries settings/model fit configuration block")
        for key in FIT_STYLE_KEYS:
            entry = fit.get(key)
            if not isinstance(entry, dict):
                raise KeyError(f"Missing model-fit style setting: {key}")
            entry["value"] = self.normalize_fit_property(key, values.get(key))
        settings.save(self.BLOCK_KEY, block)

    def normalize_fit_property(self, key, value):
        """Normalize one fit-line property through the canonical shared schema."""
        if key == "line style":
            return normalize_fit_line_style(value)
        if key == "line color":
            return normalize_color(value, "#242424")
        if key == "line width":
            return normalize_number(value, FIT_LINE_WIDTH_RANGE, FIT_LINE_WIDTH_DEFAULT)
        return value

    def normalize_property(self, key, value):
        """Normalize one property according to the canonical plugin schema."""
        if key == "marker":
            return normalize_marker(value, "o")
        if key == "line style":
            return normalize_line_style(value, "")
        if key == "marker size":
            return normalize_number(value, MARKER_SIZE_RANGE, 5.0)
        if key == "line width":
            return normalize_number(value, LINE_WIDTH_RANGE, 1.0)
        if key in ("marker color", "line color", "marker edge color"):
            fallback = "black" if key == "marker edge color" else "#1f77b4"
            return normalize_color(value, fallback)
        if key in ("marker alpha", "line alpha"):
            return normalize_number(value, (0.0, 1.0), 0.8)
        return value

    @staticmethod
    def supported_options():
        """Return schema options for validation and diagnostics."""
        return {
            "marker": MARKER_OPTIONS,
            "line style": LINE_STYLE_OPTIONS,
            "fit line style": FIT_LINE_STYLE_OPTIONS,
        }

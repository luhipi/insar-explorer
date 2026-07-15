"""Persistence coordinator for typed Time Series runtime settings."""

from copy import deepcopy

from ....external.setting_manager_ui.json_settings import JsonSettings
from ..style_config import TimeSeriesStyleConfig
from ..style_schema import MARKER_SIZE_RANGE, normalize_alpha, normalize_color, normalize_marker, normalize_number
from .model import (
    EnsembleStyleSettings, ExportSettings, FitStyleSettings,
    PlotAppearanceSettings, ReplicaSettings, ResidualStyleSettings,
    SeriesStyleSettings, TimeSeriesSettingsModel,
)


class TimeSeriesSettingsPersistence:
    """Load and save persistent Time Series defaults without exposing JSON paths."""

    BLOCK_KEY = "timeseries settings"

    def __init__(self, config_file):
        """Create a coordinator over the existing style adapter and JSON backend."""
        self.config_file = config_file
        self.style_config = TimeSeriesStyleConfig(config_file)

    @staticmethod
    def _mapping(value):
        """Return a mapping or an empty defensive fallback."""
        return value if isinstance(value, dict) else {}

    @classmethod
    def _value(cls, section, key, fallback=None):
        """Read one metadata value without trusting block or entry shape."""
        entry = cls._mapping(cls._mapping(section).get(key))
        value = entry.get("value", entry.get("default", fallback))
        return fallback if value is None else value

    @staticmethod
    def _safe_float(value, fallback, minimum=None, maximum=None):
        """Normalize one persisted numeric scalar with optional bounds."""
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return fallback
        if minimum is not None and number < minimum:
            return fallback
        if maximum is not None and number > maximum:
            return fallback
        return number

    @staticmethod
    def _safe_text(value, fallback=""):
        """Normalize one persisted text scalar."""
        return fallback if value is None or isinstance(value, (dict, list)) else str(value)

    @staticmethod
    def _safe_grid(value):
        """Normalize the constrained grid mode."""
        return value if value in {"both", "horizontal", "vertical", "none"} else "both"

    @staticmethod
    def _normalize_pair_count(value):
        """Return the supported persistent Replica pair count."""
        if isinstance(value, bool):
            return 1
        try:
            value = int(value)
        except (TypeError, ValueError, OverflowError):
            return 1
        return max(1, min(10, value))

    def _load_block(self):
        """Load a metadata block and tolerate missing or malformed content."""
        try:
            return self._mapping(JsonSettings(self.config_file).load(block_key=self.BLOCK_KEY))
        except (KeyError, TypeError, ValueError):
            return {}

    def load(self):
        """Load one normalized runtime model; session-only state starts neutral."""
        block = self._load_block()
        plot = self._mapping(block.get("time series plot"))
        residual = self._mapping(block.get("residual plot"))
        figure = self._mapping(block.get("figure"))
        export = self._mapping(block.get("export"))

        try:
            series_style = self.style_config.load_default_style()
            series = SeriesStyleSettings.from_params(series_style.params)
        except (KeyError, TypeError, ValueError):
            series = SeriesStyleSettings()
        try:
            fit = FitStyleSettings.fromParams({"model fit": self.style_config.load_default_fit_style().asParams()})
        except (KeyError, TypeError, ValueError, AttributeError):
            fit = FitStyleSettings()
        try:
            residual_style = ResidualStyleSettings.fromParams(
                {"residual plot": self.style_config.load_default_residual_style().asParams()}
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            residual_style = ResidualStyleSettings()
        try:
            ensemble = EnsembleStyleSettings.fromParams(
                {"time series plot": self.style_config.load_default_ensemble_style().asParams()}
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            ensemble = EnsembleStyleSettings()

        return TimeSeriesSettingsModel(
            series_defaults=series,
            fit_defaults=fit,
            residual_defaults=residual_style,
            ensemble_defaults=ensemble,
            replica=ReplicaSettings(
                enabled=False,
                interval_mm=2.8,
                pair_count=self._normalize_pair_count(self._value(plot, "replica pair count", 1)),
                color_1=normalize_color(self._value(plot, "replica color 1", "#ff7f0e"), "#ff7f0e"),
                color_2=normalize_color(self._value(plot, "replica color 2", "#2ca02c"), "#2ca02c"),
                opacity=normalize_alpha(self._value(plot, "replica alpha", 0.8), 0.8),
                marker=normalize_marker(self._value(plot, "replica marker", "o"), "o"),
                marker_size=normalize_number(
                    self._value(plot, "replica marker size", 5.0), MARKER_SIZE_RANGE, 5.0
                ),
            ),
            appearance=PlotAppearanceSettings(
                time_series_title=self._safe_text(self._value(plot, "title", "")),
                residual_title=self._safe_text(self._value(residual, "title", "")),
                time_series_x_label=self._safe_text(self._value(plot, "xlabel", "Date"), "Date"),
                residual_x_label=self._safe_text(self._value(residual, "xlabel", "Date"), "Date"),
                time_series_y_label=self._safe_text(self._value(plot, "ylabel", "Deformation"), "Deformation"),
                residual_y_label=self._safe_text(self._value(residual, "ylabel", "Residual"), "Residual"),
                font_size=self._safe_float(self._value(plot, "font size", 10.0), 10.0, 1.0, 200.0),
                grid=self._safe_grid(self._value(plot, "grid", "both")),
                plot_background=self._safe_text(self._value(plot, "background color", "#f5f5f5"), "#f5f5f5"),
                figure_background=self._safe_text(self._value(figure, "background color", "white"), "white"),
                date_format=self._safe_text(self._value(plot, "date format", "%Y-%m-%d"), "%Y-%m-%d"),
            ),
            export=ExportSettings.normalized(
                dpi=self._value(export, "dpi", "300"),
                aspect_ratio=self._value(export, "aspect ratio", 4.0),
                credit=self._value(export, "credit", "Powered by InSAR Explorer"),
            ),
        )

    def _save_value(self, section_name, key, value):
        """Update one metadata value while preserving every unrelated entry."""
        json_settings = JsonSettings(self.config_file)
        block = self._load_block()
        section = block.setdefault(section_name, {})
        if not isinstance(section, dict):
            section = {}
            block[section_name] = section
        entry = section.setdefault(key, {})
        if not isinstance(entry, dict):
            entry = {}
            section[key] = entry
        entry["value"] = value
        json_settings.save(self.BLOCK_KEY, block)

    def save_series_defaults(self, settings):
        """Persist primary-series defaults through the existing adapter."""
        self.style_config.save_default_style(settings.to_time_series_style())

    def save_fit_defaults(self, settings):
        """Persist fit defaults through the existing adapter."""
        self.style_config.save_default_fit_style(settings)

    def save_residual_defaults(self, settings):
        """Persist residual defaults through the existing adapter."""
        self.style_config.save_default_residual_style(settings)

    def save_ensemble_defaults(self, settings):
        """Persist ensemble defaults through the existing adapter."""
        self.style_config.save_default_ensemble_style(settings)

    def save_replica_defaults(self, settings):
        """Persist Replica defaults while retaining session activation/interval."""
        values = {
            "replica pair count": self._normalize_pair_count(settings.pair_count),
            "replica color 1": normalize_color(settings.color_1, "#ff7f0e"),
            "replica color 2": normalize_color(settings.color_2, "#2ca02c"),
            "replica alpha": normalize_alpha(settings.opacity, 0.8),
            "replica marker": normalize_marker(settings.marker, "o"),
            "replica marker size": normalize_number(settings.marker_size, MARKER_SIZE_RANGE, 5.0),
        }
        for key, value in values.items():
            self._save_value("time series plot", key, value)

    def save_appearance(self, settings):
        """Persist typed appearance values through scoped metadata writes."""
        values = {
            ("time series plot", "title"): settings.time_series_title,
            ("time series plot", "xlabel"): settings.time_series_x_label,
            ("time series plot", "ylabel"): settings.time_series_y_label,
            ("time series plot", "font size"): settings.font_size,
            ("time series plot", "grid"): self._safe_grid(settings.grid),
            ("time series plot", "background color"): settings.plot_background,
            ("time series plot", "date format"): settings.date_format,
            ("residual plot", "title"): settings.residual_title,
            ("residual plot", "xlabel"): settings.residual_x_label,
            ("residual plot", "ylabel"): settings.residual_y_label,
            ("figure", "background color"): settings.figure_background,
        }
        for (section, key), value in values.items():
            self._save_value(section, key, value)

    def save_export(self, settings):
        """Persist typed export defaults through scoped metadata writes."""
        for key, value in (("dpi", settings.dpi), ("aspect ratio", settings.aspect_ratio), ("credit", settings.credit)):
            self._save_value("export", key, value)


def build_legacy_plot_params(model, existing=None):
    """Build the temporary legacy ``PlotTs.parms`` view from runtime settings.

    TODO(phase-appearance-export): Remove when all consumers accept typed submodels.
    """
    params = deepcopy(existing) if isinstance(existing, dict) else {}
    plot = params.setdefault("time series plot", {})
    plot.update(model.series_defaults.as_params())
    plot.update(model.ensemble_defaults.asParams())
    plot.update({
        "title": model.appearance.time_series_title,
        "xlabel": model.appearance.time_series_x_label,
        "ylabel": model.appearance.time_series_y_label,
        "font size": model.appearance.font_size,
        "grid": model.appearance.grid,
        "background color": model.appearance.plot_background,
        "date format": model.appearance.date_format,
        "replica pair count": model.replica.pair_count,
        "replica color 1": model.replica.color_1,
        "replica color 2": model.replica.color_2,
        "replica alpha": model.replica.opacity,
        "replica marker": model.replica.marker,
        "replica marker size": model.replica.marker_size,
    })
    params.setdefault("model fit", {}).update(model.fit_defaults.asParams())
    residual = params.setdefault("residual plot", {})
    residual.update(model.residual_defaults.asParams())
    residual.update({
        "title": model.appearance.residual_title,
        "xlabel": model.appearance.residual_x_label,
        "ylabel": model.appearance.residual_y_label,
        "font size": model.appearance.font_size,
        "grid": model.appearance.grid,
        "background color": model.appearance.plot_background,
        "date format": model.appearance.date_format,
    })
    params.setdefault("figure", {})["background color"] = model.appearance.figure_background
    params["export"] = {
        "dpi": model.export.dpi,
        "aspect ratio": model.export.aspect_ratio,
        "credit": model.export.credit,
    }
    return params

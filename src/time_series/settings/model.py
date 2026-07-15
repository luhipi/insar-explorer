"""Pure runtime ownership model for Time Series plotting settings."""

from copy import deepcopy
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from typing import Any, Callable, ClassVar, Dict, List, Optional

from ..style_schema import (
    FIT_LINE_STYLE_DEFAULT, FIT_LINE_WIDTH_DEFAULT, FIT_LINE_WIDTH_RANGE,
    LINE_WIDTH_RANGE, MARKER_SIZE_RANGE, RESIDUAL_LINE_WIDTH_RANGE,
    RESIDUAL_MARKER_SIZE_RANGE, normalize_alpha, normalize_color,
    normalize_fit_line_style, normalize_line_style, normalize_marker,
    normalize_number, normalize_residual_line_style, normalize_residual_marker,
)
from ...models.time_series import TimeSeriesStyle
from .change_set import SettingsChangeSet


@dataclass(frozen=True)
class SeriesStyleSettings:
    """Persistent defaults used when creating a new primary series snapshot."""

    marker: str = "o"
    marker_color: str = "#1f77b4"
    marker_opacity: float = 0.8
    marker_edge_color: str = "black"
    marker_size: float = 5.0
    line_style: str = ""
    line_color: str = "#1f77b4"
    line_opacity: float = 0.8
    line_width: float = 1.0

    @classmethod
    def from_params(cls, params):
        """Build normalized settings from a legacy parameter dictionary."""
        values = params.get("time series plot", {}) if isinstance(params, dict) else {}
        return cls(
            marker=normalize_marker(values.get("marker"), "o"),
            marker_color=normalize_color(values.get("marker color"), "#1f77b4"),
            marker_opacity=normalize_alpha(values.get("marker alpha"), 0.8),
            marker_edge_color=normalize_color(values.get("marker edge color"), "black"),
            marker_size=normalize_number(values.get("marker size"), MARKER_SIZE_RANGE, 5.0),
            line_style=normalize_line_style(values.get("line style"), ""),
            line_color=normalize_color(values.get("line color"), "#1f77b4"),
            line_opacity=normalize_alpha(values.get("line alpha"), 0.8),
            line_width=normalize_number(values.get("line width"), LINE_WIDTH_RANGE, 1.0),
        )

    def as_params(self):
        """Return values using the current config/plot key names."""
        return {"marker": self.marker, "marker color": self.marker_color,
                "marker alpha": self.marker_opacity, "marker edge color": self.marker_edge_color,
                "marker size": self.marker_size, "line style": self.line_style,
                "line color": self.line_color, "line alpha": self.line_opacity,
                "line width": self.line_width}

    def to_time_series_style(self, base_params=None):
        """Create an independent legacy style for compatibility consumers."""
        params = deepcopy(base_params) if isinstance(base_params, dict) else {}
        params.setdefault("time series plot", {}).update(self.as_params())
        return TimeSeriesStyle.fromParams(params)


@dataclass(frozen=True)
class FitStyleSettings:
    """Persistent defaults for fitted time-series curves."""

    line_style: str = FIT_LINE_STYLE_DEFAULT
    line_color: str = "#242424"
    line_width: float = FIT_LINE_WIDTH_DEFAULT
    line_alpha: float = 1.0

    @classmethod
    def fromParams(cls, params):
        """Build normalized fit defaults from legacy parameters."""
        values = params.get("model fit", {}) if isinstance(params, dict) else {}
        return cls(
            line_style=normalize_fit_line_style(values.get("line style")),
            line_color=normalize_color(values.get("line color"), "#242424"),
            line_width=normalize_number(values.get("line width"), FIT_LINE_WIDTH_RANGE, FIT_LINE_WIDTH_DEFAULT),
            line_alpha=normalize_alpha(values.get("line alpha"), 1.0),
        )

    def asParams(self):
        """Return values using legacy model-fit keys."""
        return {"line style": self.line_style, "line color": self.line_color,
                "line width": self.line_width, "line alpha": self.line_alpha}


@dataclass(frozen=True)
class ResidualStyleSettings:
    """Persistent defaults for residual series."""

    marker: str = "o"
    marker_color: str = "#d62728"
    marker_edge_color: str = "black"
    marker_size: float = 5.0
    marker_alpha: float = 0.8
    line_style: str = ""
    line_color: str = "#1f77b4"
    line_width: float = 1.0
    line_alpha: float = 0.8

    @classmethod
    def fromParams(cls, params):
        """Build normalized residual defaults from legacy parameters."""
        values = params.get("residual plot", {}) if isinstance(params, dict) else {}
        return cls(
            marker=normalize_residual_marker(values.get("marker"), "o"),
            marker_color=normalize_color(values.get("marker color"), "#d62728"),
            marker_edge_color=normalize_color(values.get("marker edge color"), "black"),
            marker_size=normalize_number(values.get("marker size"), RESIDUAL_MARKER_SIZE_RANGE, 5.0),
            marker_alpha=normalize_alpha(values.get("marker alpha"), 0.8),
            line_style=normalize_residual_line_style(values.get("line style"), ""),
            line_color=normalize_color(values.get("line color"), "#1f77b4"),
            line_width=normalize_number(values.get("line width"), RESIDUAL_LINE_WIDTH_RANGE, 1.0),
            line_alpha=normalize_alpha(values.get("line alpha"), 0.8),
        )

    def asParams(self):
        """Return values using legacy residual-plot keys."""
        return {"marker": self.marker, "marker color": self.marker_color,
                "marker edge color": self.marker_edge_color,
                "marker size": self.marker_size, "marker alpha": self.marker_alpha,
                "line style": self.line_style, "line color": self.line_color,
                "line width": self.line_width, "line alpha": self.line_alpha}


@dataclass(frozen=True)
class EnsembleStyleSettings:
    """Persistent defaults for ensemble member lines and spread."""

    member_line_color: str = "gray"
    member_line_width: float = 0.5
    member_line_alpha: float = 0.5
    fill_color: str = "#1f77b4"
    fill_alpha: float = 0.2

    @classmethod
    def fromParams(cls, params):
        """Build normalized ensemble defaults from legacy parameters."""
        values = params.get("time series plot", {}) if isinstance(params, dict) else {}
        return cls(
            member_line_color=normalize_color(values.get("series line color"), "gray"),
            member_line_width=normalize_number(values.get("series line width"), (0.0, 20.0), 0.5),
            member_line_alpha=normalize_number(values.get("series line alpha"), (0.0, 1.0), 0.5),
            fill_color=normalize_color(values.get("series fill color"), "#1f77b4"),
            fill_alpha=normalize_number(values.get("series fill alpha"), (0.0, 1.0), 0.2),
        )

    def asParams(self):
        """Return values using legacy time-series plot keys."""
        return {"series line color": self.member_line_color,
                "series line width": self.member_line_width,
                "series line alpha": self.member_line_alpha,
                "series fill color": self.fill_color,
                "series fill alpha": self.fill_alpha}


@dataclass(frozen=True)
class ReplicaSettings:
    """Replica defaults plus current session activation."""

    enabled: bool = False
    interval_mm: float = 2.8
    pair_count: int = 1
    color_1: str = "#ff7f0e"
    color_2: str = "#2ca02c"
    opacity: float = 0.8
    marker: str = "o"
    marker_size: float = 5.0


@dataclass(frozen=True)
class AxisManualRange:
    """Optional lower and upper limits for one manual axis."""

    lower: Optional[float] = None
    upper: Optional[float] = None


@dataclass(frozen=True)
class YAxisSettings:
    """Session-only Y-axis policy, manual ranges, and transient viewport state."""

    policy: str = "from_data"
    series_manual: AxisManualRange = field(default_factory=AxisManualRange)
    residual_manual: AxisManualRange = field(default_factory=AxisManualRange)
    series_custom_view: bool = False
    residual_custom_view: bool = False


@dataclass(frozen=True)
class XAxisSettings:
    """Session-only X-axis policy, manual date range, and transient viewport state."""

    policy: str = "from_data"
    manual_start: Optional[datetime] = None
    manual_end: Optional[datetime] = None
    custom_view: bool = False


@dataclass(frozen=True)
class AppearanceSettings:
    """Persistent plot-wide appearance defaults currently represented in config."""

    time_series_title: str = ""
    residual_title: str = ""
    time_series_x_label: str = "Date"
    residual_x_label: str = "Date"
    time_series_y_label: str = "Deformation"
    residual_y_label: str = "Residual"
    font_size: float = 10.0
    grid_mode: str = "both"
    plot_background: str = "#f5f5f5"
    figure_background: str = "white"
    date_format: Optional[str] = "%Y-%m-%d"

    GRID_MODES: ClassVar[tuple] = ("both", "horizontal", "vertical", "none")

    def __post_init__(self):
        """Normalize the canonical grid mode without introducing a Boolean alias."""
        object.__setattr__(self, "grid_mode", self.normalize_grid_mode(self.grid_mode))

    @classmethod
    def normalize_grid_mode(cls, value):
        """Return one supported canonical grid mode, defaulting invalid values to both."""
        return value if value in cls.GRID_MODES else "both"


@dataclass(frozen=True)
class ExportSettings:
    """Persistent normalized defaults for plot export."""

    dpi: str = "300"
    aspect_ratio: float = 4.0
    credit: str = "Powered by InSAR Explorer"

    DPI_OPTIONS = ("72", "150", "300", "600", "1200")

    @classmethod
    def normalized(cls, dpi=None, aspect_ratio=None, credit=None):
        """Build settings with schema-compatible normalization."""
        dpi = str(dpi) if dpi is not None else cls().dpi
        if dpi not in cls.DPI_OPTIONS:
            dpi = cls().dpi
        try:
            aspect_ratio = float(aspect_ratio)
        except (TypeError, ValueError, OverflowError):
            aspect_ratio = cls().aspect_ratio
        aspect_ratio = max(1.0, min(10.0, aspect_ratio))
        credit = cls().credit if credit is None else str(credit)
        return cls(dpi=dpi, aspect_ratio=aspect_ratio, credit=credit)


@dataclass
class TimeSeriesSettingsModel:
    """Authoritative runtime settings for Time Series plotting."""

    series_defaults: SeriesStyleSettings = field(default_factory=SeriesStyleSettings)
    fit_defaults: FitStyleSettings = field(default_factory=FitStyleSettings)
    residual_defaults: ResidualStyleSettings = field(default_factory=ResidualStyleSettings)
    ensemble_defaults: EnsembleStyleSettings = field(default_factory=EnsembleStyleSettings)
    replica: ReplicaSettings = field(default_factory=ReplicaSettings)
    y_axis: YAxisSettings = field(default_factory=YAxisSettings)
    x_axis: XAxisSettings = field(default_factory=XAxisSettings)
    appearance: AppearanceSettings = field(default_factory=AppearanceSettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    _listeners: List[Callable[[SettingsChangeSet], None]] = field(default_factory=list, init=False, repr=False)
    _batch_depth: int = field(default=0, init=False, repr=False)
    _batched_changes: SettingsChangeSet = field(default_factory=SettingsChangeSet, init=False, repr=False)

    def subscribe(self, callback):
        """Register a callback and return an unsubscribe function."""
        self._listeners.append(callback)
        return lambda: self._listeners.remove(callback) if callback in self._listeners else None

    def replace_domain(self, domain, value):
        """Replace one typed submodel and report precisely what changed."""
        old = getattr(self, domain)
        if old == value:
            return SettingsChangeSet()
        setattr(self, domain, deepcopy(value))
        old_values = asdict(old)
        new_values = asdict(value)
        changed = [key for key in set(old_values) | set(new_values) if old_values.get(key) != new_values.get(key)]
        change = SettingsChangeSet.for_properties(domain, changed)
        if self._batch_depth:
            self._batched_changes = self._batched_changes.merge(change)
        else:
            self.notify(change)
        return change


    def notify(self, change):
        """Notify listeners once for one completed logical update."""
        if not change.domains:
            return
        for callback in tuple(self._listeners):
            callback(change)

    @contextmanager
    def batch_update(self):
        """Merge multiple domain replacements into one listener notification."""
        self._batch_depth += 1
        try:
            yield self
        finally:
            self._batch_depth -= 1
            if self._batch_depth == 0 and self._batched_changes.domains:
                change = self._batched_changes
                self._batched_changes = SettingsChangeSet()
                self.notify(change)

    def replace_domains(self, values):
        """Replace multiple submodels and return one merged change set."""
        merged = SettingsChangeSet()
        with self.batch_update():
            for domain, value in values.items():
                merged = merged.merge(self.replace_domain(domain, value))
        return merged

    def update_property(self, domain, property_name, value):
        """Update one property through immutable submodel replacement."""
        current = getattr(self, domain)
        return self.replace_domain(domain, replace(current, **{property_name: value}))

    def persistent_payload(self):
        """Return persistent domains only; session policies and manual ranges are excluded."""
        return {
            "series_defaults": self.series_defaults.as_params(),
            "fit_defaults": self.fit_defaults.asParams(),
            "residual_defaults": self.residual_defaults.asParams(),
            "ensemble_defaults": self.ensemble_defaults.asParams(),
            "replica_defaults": {"interval_mm": self.replica.interval_mm, "pair_count": self.replica.pair_count},
            "appearance": asdict(self.appearance),
            "export": asdict(self.export),
        }

    def copy(self):
        """Return a defensive model copy without sharing listeners."""
        return TimeSeriesSettingsModel(**{name: deepcopy(getattr(self, name)) for name in (
            "series_defaults", "fit_defaults", "residual_defaults", "ensemble_defaults",
            "replica", "y_axis", "x_axis", "appearance", "export")})

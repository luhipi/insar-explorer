"""Selection-aware availability for Time Series style layers."""

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class TimeSeriesStyleAvailability:
    """Describe editable style layers for the current snapshot selection."""

    selected_count: int = 0
    series_target_count: int = 0
    fit_target_count: int = 0
    residual_target_count: int = 0
    ensemble_target_count: int = 0

    @property
    def series_available(self):
        return self.series_target_count > 0

    @property
    def fit_available(self):
        return self.fit_target_count > 0

    @property
    def residual_available(self):
        return self.residual_target_count > 0

    @property
    def ensemble_available(self):
        return self.ensemble_target_count > 0

    @classmethod
    def fromSelection(cls, snapshots: Iterable, fit_enabled=False, residual_enabled=False):
        """Build availability from model/controller state, never toolbar widgets."""
        selected: Tuple = tuple(snapshots or ())
        count = len(selected)
        ensemble_count = sum(
            1 for snapshot in selected
            if getattr(snapshot, "data", None) is not None
            and snapshot.data.hasEnsembleData()
        )
        return cls(
            selected_count=count,
            series_target_count=count,
            fit_target_count=count if fit_enabled else 0,
            residual_target_count=count if residual_enabled and fit_enabled else 0,
            ensemble_target_count=ensemble_count,
        )

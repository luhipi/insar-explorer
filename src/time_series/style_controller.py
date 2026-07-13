"""Selection-oriented time-series style mutation service."""

from copy import deepcopy
from typing import Iterable

from ..models.time_series import (
    TimeSeriesSnapshot,
    TimeSeriesStyle,
    randomTimeSeriesColor,
)


class TimeSeriesStyleController:
    """Apply property-level style changes to explicitly selected snapshots."""

    STYLE_KEYS = {
        "marker_type": "marker",
        "marker_color": "marker color",
        "marker_size": "marker size",
        "line_type": "line style",
        "line_color": "line color",
        "line_width": "line width",
    }

    def selectedSeriesStyles(self, snapshots: Iterable[TimeSeriesSnapshot]):
        """Return styles for explicit selection targets without assuming ordering."""
        return [snapshot.style for snapshot in snapshots]

    def mixedProperties(self, snapshots: Iterable[TimeSeriesSnapshot]):
        """Return editable property names whose values differ across selected styles."""
        snapshots = list(snapshots)
        if len(snapshots) < 2:
            return set()
        mixed = set()
        for property_name, key in self.STYLE_KEYS.items():
            values = [repr(snapshot.style.params.get("time series plot", {}).get(key)) for snapshot in snapshots]
            if len(set(values)) > 1:
                mixed.add(property_name)
        return mixed

    def applyProperty(self, snapshots: Iterable[TimeSeriesSnapshot], property_name, value):
        """Apply one style property to every supplied snapshot and return changed targets."""
        key = self.STYLE_KEYS[property_name]
        changed = []
        for snapshot in snapshots:
            params = deepcopy(snapshot.style.params)
            params.setdefault("time series plot", {})[key] = value
            snapshot.style = TimeSeriesStyle.fromParams(
                params,
                label=snapshot.style.label,
                visible=snapshot.style.visible,
                z_order=snapshot.style.z_order,
            )
            changed.append(snapshot)
        return changed

    def randomizeColor(self, snapshots: Iterable[TimeSeriesSnapshot]):
        """Apply one random coupled marker/line color to each selected snapshot."""
        changed = []
        for snapshot in snapshots:
            color = randomTimeSeriesColor()
            params = deepcopy(snapshot.style.params)
            plot = params.setdefault("time series plot", {})
            plot["marker color"] = color
            plot["line color"] = color
            snapshot.style = TimeSeriesStyle.fromParams(
                params,
                label=snapshot.style.label,
                visible=snapshot.style.visible,
                z_order=snapshot.style.z_order,
            )
            changed.append(snapshot)
        return changed

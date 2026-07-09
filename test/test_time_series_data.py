from dataclasses import FrozenInstanceError
from datetime import datetime

import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from models.time_series import (
    TimeSeriesData,
    TimeSeriesGraphics,
    TimeSeriesSnapshot,
    TimeSeriesStyle,
    buildTimeSeriesData,
)


def _dates():
    return np.array([
        datetime(2020, 1, 3),
        datetime(2020, 1, 1),
        datetime(2020, 1, 2),
    ])


def _sorted_date_strings(series):
    return [d.strftime('%Y-%m-%d') for d in series.dates]


def test_build_time_series_data_sorts_dates_and_reorders_values():
    series = buildTimeSeriesData(dates=_dates(), ts_values=[3.0, 1.0, 2.0], ref_values=[0.3, 0.1, 0.2])

    assert _sorted_date_strings(series) == ["2020-01-01", "2020-01-02", "2020-01-03"]
    np.testing.assert_allclose(series.ts_values[:, 0], [1.0, 2.0, 3.0])
    np.testing.assert_allclose(series.ref_values[:, 0], [0.1, 0.2, 0.3])
    np.testing.assert_allclose(series.plot_values, [0.9, 1.8, 2.7])


def test_single_series_with_scalar_zero_reference():
    series = buildTimeSeriesData(dates=_dates(), ts_values=[3.0, 1.0, 2.0], ref_values=0)

    np.testing.assert_allclose(series.ref_values[:, 0], [0.0, 0.0, 0.0])
    np.testing.assert_allclose(series.plot_values, [1.0, 2.0, 3.0])
    assert series.min_plot_values is None
    assert series.max_plot_values is None
    assert series.plot_multiple_values is None


def test_single_series_with_one_reference_value_per_date():
    series = buildTimeSeriesData(dates=_dates(), ts_values=[3.0, 1.0, 2.0], ref_values=[30.0, 10.0, 20.0])

    np.testing.assert_allclose(series.ref_values[:, 0], [10.0, 20.0, 30.0])
    np.testing.assert_allclose(series.plot_values, [-9.0, -18.0, -27.0])


def test_multiple_time_series_columns_with_one_reference_value_per_date():
    ts_values = np.array([[3.0, 6.0], [1.0, 4.0], [2.0, 5.0]])
    ref_values = np.array([0.3, 0.1, 0.2])

    series = buildTimeSeriesData(dates=_dates(), ts_values=ts_values, ref_values=ref_values)

    expected = np.array([
        [1.0 - 0.1, 4.0 - 0.1],
        [2.0 - 0.2, 5.0 - 0.2],
        [3.0 - 0.3, 6.0 - 0.3],
    ])
    np.testing.assert_allclose(series.plot_multiple_values, expected)
    np.testing.assert_allclose(series.min_plot_values, np.min(expected, axis=1))
    np.testing.assert_allclose(series.max_plot_values, np.max(expected, axis=1))
    np.testing.assert_allclose(series.plot_values, np.mean(expected, axis=1))


def test_multiple_time_series_columns_with_multiple_reference_columns():
    ts_values = np.array([[3.0, 6.0], [1.0, 4.0], [2.0, 5.0]])
    ref_values = np.array([[0.3, 0.9], [0.1, 0.7], [0.2, 0.8]])

    series = buildTimeSeriesData(dates=_dates(), ts_values=ts_values, ref_values=ref_values)

    expected = np.array([
        [1.0 - 0.4, 4.0 - 0.4],
        [2.0 - 0.5, 5.0 - 0.5],
        [3.0 - 0.6, 6.0 - 0.6],
    ])
    np.testing.assert_allclose(series.plot_multiple_values, expected)
    np.testing.assert_allclose(series.plot_values, np.mean(expected, axis=1))


def test_already_sorted_input_is_preserved():
    dates = np.array([datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)])
    series = buildTimeSeriesData(dates=dates, ts_values=[1.0, 2.0, 3.0], ref_values=0)

    assert _sorted_date_strings(series) == ["2020-01-01", "2020-01-02", "2020-01-03"]
    np.testing.assert_allclose(series.plot_values, [1.0, 2.0, 3.0])


def test_invalid_mismatched_ts_row_count_raises_value_error():
    with pytest.raises(ValueError, match="ts_values row count"):
        buildTimeSeriesData(dates=_dates(), ts_values=[1.0, 2.0], ref_values=0)


def test_invalid_mismatched_ref_row_count_raises_value_error():
    with pytest.raises(ValueError, match="ref_values row count"):
        buildTimeSeriesData(dates=_dates(), ts_values=[1.0, 2.0, 3.0], ref_values=[1.0, 2.0])


def test_style_params_are_deep_copied():
    params = {"time series plot": {"marker color": "red"}}
    style = TimeSeriesStyle.fromParams(params)
    params["time series plot"]["marker color"] = "blue"

    assert style.params["time series plot"]["marker color"] == "red"


def test_graphics_list_fields_are_independent_per_instance():
    a = TimeSeriesGraphics()
    b = TimeSeriesGraphics()

    a.plot_multiple_lines.append(object())
    a.main_y_data.append([1, 2, 3])

    assert b.plot_multiple_lines == []
    assert b.main_y_data == []


def test_time_series_data_is_frozen_and_arrays_are_read_only():
    series = buildTimeSeriesData(dates=_dates(), ts_values=[3.0, 1.0, 2.0], ref_values=0)

    with pytest.raises(FrozenInstanceError):
        series.residuals_values = np.array([1.0, 2.0, 3.0])
    with pytest.raises(ValueError):
        series.plot_values[0] = 999.0
    with pytest.raises(ValueError):
        series.ts_values[0, 0] = 999.0


def test_with_residuals_returns_new_instance_and_read_only_residuals():
    series = buildTimeSeriesData(dates=_dates(), ts_values=[3.0, 1.0, 2.0], ref_values=0)

    updated = series.withResiduals([0.1, 0.2, 0.3])

    assert series.residuals_values is None
    np.testing.assert_allclose(updated.residuals_values, [0.1, 0.2, 0.3])
    with pytest.raises(ValueError):
        updated.residuals_values[0] = 999.0


def test_snapshot_owns_data_style_and_graphics():
    data = buildTimeSeriesData(dates=_dates(), ts_values=[3.0, 1.0, 2.0], ref_values=0)
    style = TimeSeriesStyle.fromParams({"time series plot": {}})
    graphics = TimeSeriesGraphics(scatter=object())

    snapshot = TimeSeriesSnapshot(data=data, style=style, graphics=graphics)

    assert snapshot.data is data
    assert snapshot.style is style
    assert snapshot.graphics is graphics


def test_legacy_graphics_keys_shape_without_qgis():
    graphics = TimeSeriesGraphics(
        scatter="scatter",
        line="line",
        fit_plot="fit",
        residual_scatter="residual_scatter",
        residual_line="residual_line",
        main_y_data=[[1, 2]],
        residual_y_data=[[0, 0]],
    )
    main = {
        "scatter": graphics.scatter,
        "line": graphics.line,
        "plot_multiple_fill": graphics.plot_multiple_fill,
        "plot_multiple_lines": graphics.plot_multiple_lines,
        "replicate_up": graphics.replicate_up,
        "replicate_dn": graphics.replicate_dn,
        "fit_plot_list": graphics.fit_plot,
        "main_y_data": graphics.main_y_data,
    }
    residuals = {
        "residual_scatter": graphics.residual_scatter,
        "residual_line": graphics.residual_line,
        "residual_y_data": graphics.residual_y_data,
    }

    assert set(main) == {
        "scatter", "line", "plot_multiple_fill", "plot_multiple_lines",
        "replicate_up", "replicate_dn", "fit_plot_list", "main_y_data",
    }
    assert set(residuals) == {"residual_scatter", "residual_line", "residual_y_data"}


def test_update_removal_keeps_fresh_settings_for_latest_series_redraw():
    """Regression guard for hold-on update: do not restore previous snapshot style in update removal."""
    plot_timeseries = Path(__file__).resolve().parents[1] / "src" / "plot_timeseries.py"
    source = plot_timeseries.read_text()
    method_source = source.split("    def _remove_rendered_snapshot_for_update", 1)[1].split("    def _remove_snapshot_graphics", 1)[0]

    assert "deepcopy(restored_snapshot.style.params)" not in method_source
    assert "self.parms =" not in method_source
    assert "settings-driven update must preserve" in method_source

import pandas as pd

from src.evaluation import (
    build_route_comparison,
    filter_points_by_radius,
    summarize_route_accuracy,
)


def test_build_route_comparison_adds_error_distance() -> None:
    actual = pd.DataFrame(
        [
            {"scan_id": "scan_01", "latitude": 48.880000, "longitude": 8.700000},
            {"scan_id": "scan_02", "latitude": 48.880100, "longitude": 8.700100},
        ]
    )
    estimated = pd.DataFrame(
        [
            {
                "scan_id": "scan_01",
                "latitude": 48.880000,
                "longitude": 8.700000,
                "matched_access_points": 4,
                "residual_rmse": 5.0,
            },
            {
                "scan_id": "scan_02",
                "latitude": 48.880150,
                "longitude": 8.700100,
                "matched_access_points": 3,
                "residual_rmse": 8.0,
            },
        ]
    )

    comparison = build_route_comparison(actual, estimated)

    assert len(comparison) == 2
    assert comparison.loc[0, "error_m"] == 0
    assert comparison.loc[1, "error_m"] > 0
    assert {"actual_latitude", "estimated_latitude", "error_m"}.issubset(comparison.columns)


def test_filter_points_by_radius_keeps_only_nearby_points() -> None:
    points = pd.DataFrame(
        [
            {"name": "near", "latitude": 48.880000, "longitude": 8.700100},
            {"name": "far", "latitude": 48.882000, "longitude": 8.700000},
        ]
    )

    filtered = filter_points_by_radius(48.880000, 8.700000, points, radius_m=60)

    assert filtered["name"].tolist() == ["near"]


def test_summarize_route_accuracy_returns_core_metrics() -> None:
    comparison = pd.DataFrame(
        [
            {"error_m": 10.0},
            {"error_m": 20.0},
            {"error_m": 30.0},
        ]
    )

    summary = summarize_route_accuracy(comparison)

    assert summary["compared_scans"] == 3
    assert summary["mean_error_m"] == 20.0
    assert summary["median_error_m"] == 20.0
    assert summary["max_error_m"] == 30.0

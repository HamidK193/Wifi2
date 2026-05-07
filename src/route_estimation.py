from pathlib import Path

import pandas as pd

from src.fingerprint_localization import get_scan_input_observations
from src.localization_logic import calculate_distance_m, estimate_position_from_access_points
from src.road_constraints import snap_position_to_nearest_road


ROUTE_ESTIMATE_COLUMNS = [
    "scan_id",
    "timestamp",
    "actual_latitude",
    "actual_longitude",
    "raw_estimated_latitude",
    "raw_estimated_longitude",
    "estimated_latitude",
    "estimated_longitude",
    "matched_access_points",
    "residual_rmse",
    "snap_distance_m",
    "error_m",
    "method",
]


def build_wifi_route_from_scan_positions(
    calibration_dataframe: pd.DataFrame,
    scan_positions: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    min_matches: int = 2,
) -> pd.DataFrame:
    if calibration_dataframe.empty or scan_positions.empty:
        return pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS)

    actual_positions = _build_actual_scan_positions(calibration_dataframe)
    estimated_positions = scan_positions.copy()
    if "matched_access_points" in estimated_positions.columns:
        estimated_positions = estimated_positions.loc[
            estimated_positions["matched_access_points"] >= min_matches
        ].copy()

    merged = actual_positions.merge(
        estimated_positions,
        on="scan_id",
        how="inner",
        suffixes=("_actual", "_estimated"),
    )
    if merged.empty:
        return pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS)

    rows: list[dict[str, object]] = []
    for row in merged.itertuples(index=False):
        raw_latitude = float(row.latitude_estimated)
        raw_longitude = float(row.longitude_estimated)
        snapped_position = snap_position_to_nearest_road(raw_latitude, raw_longitude, osm_map)
        error_m = calculate_distance_m(
            float(row.latitude_actual),
            float(row.longitude_actual),
            snapped_position["latitude"],
            snapped_position["longitude"],
            float(row.latitude_actual),
        )
        rows.append(
            {
                "scan_id": row.scan_id,
                "timestamp": row.timestamp_actual,
                "actual_latitude": float(row.latitude_actual),
                "actual_longitude": float(row.longitude_actual),
                "raw_estimated_latitude": raw_latitude,
                "raw_estimated_longitude": raw_longitude,
                "estimated_latitude": snapped_position["latitude"],
                "estimated_longitude": snapped_position["longitude"],
                "matched_access_points": int(getattr(row, "matched_access_points", 0)),
                "residual_rmse": float(getattr(row, "residual_rmse", 0.0)),
                "snap_distance_m": snapped_position["snap_distance_m"],
                "error_m": error_m,
                "method": "precomputed_wifi_multilateration",
            }
        )

    return pd.DataFrame(rows, columns=ROUTE_ESTIMATE_COLUMNS).sort_values("timestamp").reset_index(drop=True)


def build_wifi_route_estimates(
    calibration_dataframe: pd.DataFrame,
    access_points: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    min_matches: int = 2,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if calibration_dataframe.empty or access_points.empty:
        return pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS)

    actual_positions = _build_actual_scan_positions(calibration_dataframe)
    for actual_row in actual_positions.itertuples(index=False):
        input_observations = get_scan_input_observations(calibration_dataframe, actual_row.scan_id)
        estimate = estimate_position_from_access_points(
            access_points,
            input_observations,
            min_matches=min_matches,
        )
        if estimate is None:
            continue

        snapped_position = snap_position_to_nearest_road(
            estimate["latitude"],
            estimate["longitude"],
            osm_map,
        )
        error_m = calculate_distance_m(
            actual_row.latitude,
            actual_row.longitude,
            snapped_position["latitude"],
            snapped_position["longitude"],
            actual_row.latitude,
        )
        rows.append(
            {
                "scan_id": actual_row.scan_id,
                "timestamp": actual_row.timestamp,
                "actual_latitude": actual_row.latitude,
                "actual_longitude": actual_row.longitude,
                "raw_estimated_latitude": estimate["latitude"],
                "raw_estimated_longitude": estimate["longitude"],
                "estimated_latitude": snapped_position["latitude"],
                "estimated_longitude": snapped_position["longitude"],
                "matched_access_points": estimate["matched_networks"],
                "residual_rmse": estimate["residual_rmse"],
                "snap_distance_m": snapped_position["snap_distance_m"],
                "error_m": error_m,
                "method": estimate.get("method", "unknown"),
            }
        )

    if not rows:
        return pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS)

    return pd.DataFrame(rows, columns=ROUTE_ESTIMATE_COLUMNS).sort_values("timestamp").reset_index(drop=True)


def summarize_wifi_route(route_estimates: pd.DataFrame) -> dict[str, float | int | None]:
    if route_estimates.empty:
        return {
            "estimated_scans": 0,
            "mean_error_m": None,
            "median_error_m": None,
            "max_error_m": None,
        }

    return {
        "estimated_scans": int(len(route_estimates)),
        "mean_error_m": float(route_estimates["error_m"].mean()),
        "median_error_m": float(route_estimates["error_m"].median()),
        "max_error_m": float(route_estimates["error_m"].max()),
    }


def save_route_estimates(route_estimates: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    route_estimates.to_csv(path, index=False)
    return path


def _build_actual_scan_positions(calibration_dataframe: pd.DataFrame) -> pd.DataFrame:
    return (
        calibration_dataframe.groupby(["scan_id", "timestamp"], as_index=False)
        .agg(
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
        )
        .dropna(subset=["latitude", "longitude"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

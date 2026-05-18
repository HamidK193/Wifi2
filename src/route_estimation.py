from pathlib import Path

import pandas as pd

from src.fingerprint_localization import get_scan_input_observations
from src.localization_logic import calculate_distance_m, estimate_position_from_access_points
from src.road_constraints import match_route_to_walkable_roads, snap_position_to_nearest_road


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
ROUTE_QUALITY_COLUMNS = ROUTE_ESTIMATE_COLUMNS + [
    "gps_jump_m",
    "wifi_jump_m",
    "is_outlier",
    "outlier_reason",
]
GPS_ROUTE_COLUMNS = [
    "scan_id",
    "timestamp",
    "raw_latitude",
    "raw_longitude",
    "latitude",
    "longitude",
    "snap_distance_m",
    "road_type",
    "snapped",
    "segment_id",
    "match_score",
    "candidate_count",
]
DEFAULT_MISSING_RSSI = -100.0


def build_gps_route_raw(calibration_dataframe: pd.DataFrame) -> pd.DataFrame:
    actual_positions = _build_actual_scan_positions(calibration_dataframe)
    if actual_positions.empty:
        return pd.DataFrame(columns=["scan_id", "timestamp", "latitude", "longitude"])
    return actual_positions.loc[:, ["scan_id", "timestamp", "latitude", "longitude"]].reset_index(drop=True)


def build_gps_route_matched(
    calibration_dataframe: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    max_candidate_distance_m: float = 30.0,
) -> pd.DataFrame:
    raw_route = build_gps_route_raw(calibration_dataframe)
    if raw_route.empty:
        return pd.DataFrame(columns=GPS_ROUTE_COLUMNS)

    matched = match_route_to_walkable_roads(
        raw_route,
        osm_map,
        latitude_column="latitude",
        longitude_column="longitude",
        max_candidate_distance_m=max_candidate_distance_m,
    )
    return matched.loc[:, [column for column in GPS_ROUTE_COLUMNS if column in matched.columns]].reset_index(drop=True)


def build_wifi_route_from_scan_positions(
    calibration_dataframe: pd.DataFrame,
    scan_positions: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    min_matches: int = 2,
    max_snap_distance_m: float = 60.0,
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
        snapped_position = snap_position_to_nearest_road(
            raw_latitude,
            raw_longitude,
            osm_map,
            max_snap_distance_m=max_snap_distance_m,
        )
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
    max_snap_distance_m: float = 60.0,
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
            max_snap_distance_m=max_snap_distance_m,
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


def estimate_scan_position_wknn(
    reference_dataframe: pd.DataFrame,
    input_observations: pd.DataFrame,
    *,
    k: int = 5,
    min_matches: int = 3,
    missing_rssi: float = DEFAULT_MISSING_RSSI,
) -> dict[str, object] | None:
    if reference_dataframe.empty or input_observations.empty:
        return None

    input_by_network = (
        input_observations.groupby("network_id", as_index=False)
        .agg(rssi=("rssi", "mean"))
        .set_index("network_id")["rssi"]
        .to_dict()
    )
    candidate_rows: list[dict[str, object]] = []

    for scan_id, scan_rows in reference_dataframe.groupby("scan_id"):
        reference_by_network = (
            scan_rows.groupby("network_id", as_index=False)
            .agg(rssi=("rssi", "mean"))
            .set_index("network_id")["rssi"]
            .to_dict()
        )
        common_networks = sorted(set(input_by_network).intersection(reference_by_network))
        if len(common_networks) < min_matches:
            continue

        squared_distance = 0.0
        for network_id in common_networks:
            input_rssi = float(input_by_network.get(network_id, missing_rssi))
            reference_rssi = float(reference_by_network.get(network_id, missing_rssi))
            # Stronger APs are more informative, but keep the weight bounded.
            weight = 1.0 + max(input_rssi, reference_rssi, -90.0) + 90.0
            squared_distance += weight * (input_rssi - reference_rssi) ** 2

        mean_distance = (squared_distance / len(common_networks)) ** 0.5
        position = _get_scan_position_from_reference(scan_rows)
        if position is None:
            continue
        candidate_rows.append(
            {
                "scan_id": scan_id,
                "latitude": position["latitude"],
                "longitude": position["longitude"],
                "rssi_distance": float(mean_distance),
                "matched_access_points": int(len(common_networks)),
            }
        )

    if not candidate_rows:
        return None

    candidates = (
        pd.DataFrame(candidate_rows)
        .sort_values(["rssi_distance", "matched_access_points"], ascending=[True, False])
        .head(k)
        .copy()
    )
    weights = 1.0 / (candidates["rssi_distance"].clip(lower=1.0) ** 2)
    latitude = float((candidates["latitude"] * weights).sum() / weights.sum())
    longitude = float((candidates["longitude"] * weights).sum() / weights.sum())
    return {
        "latitude": latitude,
        "longitude": longitude,
        "matched_access_points": int(candidates["matched_access_points"].max()),
        "residual_rmse": float(candidates["rssi_distance"].mean()),
        "method": "wknn_fingerprinting",
    }


def build_wknn_route_comparison(
    calibration_dataframe: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    k: int = 5,
    min_matches: int = 3,
    max_snap_distance_m: float = 60.0,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if calibration_dataframe.empty:
        return pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS)

    fingerprints = _build_scan_fingerprints(calibration_dataframe)
    for actual_row in fingerprints:
        estimate = _estimate_scan_position_wknn_from_fingerprints(
            actual_row,
            fingerprints,
            k=k,
            min_matches=min_matches,
        )
        if estimate is None:
            continue

        snapped_position = snap_position_to_nearest_road(
            estimate["latitude"],
            estimate["longitude"],
            osm_map,
            max_snap_distance_m=max_snap_distance_m,
        )
        error_m = calculate_distance_m(
            float(actual_row["latitude"]),
            float(actual_row["longitude"]),
            snapped_position["latitude"],
            snapped_position["longitude"],
            float(actual_row["latitude"]),
        )
        rows.append(
            {
                "scan_id": actual_row["scan_id"],
                "timestamp": actual_row["timestamp"],
                "actual_latitude": actual_row["latitude"],
                "actual_longitude": actual_row["longitude"],
                "raw_estimated_latitude": estimate["latitude"],
                "raw_estimated_longitude": estimate["longitude"],
                "estimated_latitude": snapped_position["latitude"],
                "estimated_longitude": snapped_position["longitude"],
                "matched_access_points": estimate["matched_access_points"],
                "residual_rmse": estimate["residual_rmse"],
                "snap_distance_m": snapped_position["snap_distance_m"],
                "error_m": error_m,
                "method": estimate["method"],
            }
        )

    if not rows:
        return pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS)

    route = pd.DataFrame(rows, columns=ROUTE_ESTIMATE_COLUMNS).sort_values("timestamp").reset_index(drop=True)
    smoothed_route = smooth_route_positions(route)
    return _snap_route_estimates_to_roads(
        smoothed_route,
        osm_map,
        max_snap_distance_m=max_snap_distance_m,
    )


def build_route_comparison_with_matched_gps(
    route_comparison: pd.DataFrame,
    gps_route_matched: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    max_candidate_distance_m: float = 60.0,
) -> pd.DataFrame:
    if route_comparison.empty or gps_route_matched.empty:
        return pd.DataFrame(columns=list(route_comparison.columns))

    gps_reference = gps_route_matched.rename(
        columns={
            "raw_latitude": "raw_actual_latitude",
            "raw_longitude": "raw_actual_longitude",
            "latitude": "matched_actual_latitude",
            "longitude": "matched_actual_longitude",
            "snap_distance_m": "gps_snap_distance_m",
            "road_type": "gps_road_type",
        }
    )
    gps_columns = [
        "scan_id",
        "raw_actual_latitude",
        "raw_actual_longitude",
        "matched_actual_latitude",
        "matched_actual_longitude",
        "gps_snap_distance_m",
        "gps_road_type",
    ]
    available_gps_columns = [column for column in gps_columns if column in gps_reference.columns]
    merged = route_comparison.merge(
        gps_reference.loc[:, available_gps_columns],
        on="scan_id",
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame(columns=list(route_comparison.columns))

    wifi_source = merged.loc[:, ["scan_id", "timestamp", "raw_estimated_latitude", "raw_estimated_longitude"]].rename(
        columns={
            "raw_estimated_latitude": "latitude",
            "raw_estimated_longitude": "longitude",
        }
    )
    wifi_matched = match_route_to_walkable_roads(
        wifi_source,
        osm_map,
        latitude_column="latitude",
        longitude_column="longitude",
        max_candidate_distance_m=max_candidate_distance_m,
    )
    wifi_reference = wifi_matched.rename(
        columns={
            "latitude": "matched_estimated_latitude",
            "longitude": "matched_estimated_longitude",
            "snap_distance_m": "wifi_snap_distance_m",
            "road_type": "wifi_road_type",
        }
    )
    wifi_columns = ["scan_id", "matched_estimated_latitude", "matched_estimated_longitude", "wifi_snap_distance_m", "wifi_road_type"]
    merged = merged.merge(
        wifi_reference.loc[:, wifi_columns],
        on="scan_id",
        how="inner",
    )
    if merged.empty:
        return pd.DataFrame(columns=list(route_comparison.columns))

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        actual_latitude = float(row["matched_actual_latitude"])
        actual_longitude = float(row["matched_actual_longitude"])
        estimated_latitude = float(row["matched_estimated_latitude"])
        estimated_longitude = float(row["matched_estimated_longitude"])
        rows.append(
            {
                **row.to_dict(),
                "actual_latitude": actual_latitude,
                "actual_longitude": actual_longitude,
                "estimated_latitude": estimated_latitude,
                "estimated_longitude": estimated_longitude,
                "snap_distance_m": row["wifi_snap_distance_m"],
                "error_m": calculate_distance_m(
                    actual_latitude,
                    actual_longitude,
                    estimated_latitude,
                    estimated_longitude,
                    actual_latitude,
                ),
                "method": f"{row['method']}_route_matched",
            }
        )

    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


def smooth_route_positions(route_comparison: pd.DataFrame, *, alpha: float = 0.35) -> pd.DataFrame:
    if route_comparison.empty:
        return route_comparison.copy()

    route = route_comparison.sort_values("timestamp").reset_index(drop=True).copy()
    smoothed_latitudes: list[float] = []
    smoothed_longitudes: list[float] = []

    last_latitude: float | None = None
    last_longitude: float | None = None
    for row in route.itertuples(index=False):
        latitude = float(row.estimated_latitude)
        longitude = float(row.estimated_longitude)
        if last_latitude is None or last_longitude is None:
            smoothed_latitude = latitude
            smoothed_longitude = longitude
        else:
            smoothed_latitude = alpha * latitude + (1 - alpha) * last_latitude
            smoothed_longitude = alpha * longitude + (1 - alpha) * last_longitude

        smoothed_latitudes.append(smoothed_latitude)
        smoothed_longitudes.append(smoothed_longitude)
        last_latitude = smoothed_latitude
        last_longitude = smoothed_longitude

    route["estimated_latitude"] = smoothed_latitudes
    route["estimated_longitude"] = smoothed_longitudes
    route["error_m"] = route.apply(
        lambda row: calculate_distance_m(
            row["actual_latitude"],
            row["actual_longitude"],
            row["estimated_latitude"],
            row["estimated_longitude"],
            row["actual_latitude"],
        ),
        axis=1,
    )
    route["method"] = route["method"].astype(str) + "_smoothed"
    return route


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


def summarize_route_quality(route_estimates: pd.DataFrame) -> dict[str, object]:
    if route_estimates.empty:
        return {
            "quality_label": "schwach",
            "p90_error_m": None,
            "used_scans": 0,
        }

    median_error = float(route_estimates["error_m"].median())
    p90_error = float(route_estimates["error_m"].quantile(0.9))
    if median_error <= 20 and p90_error <= 50:
        quality_label = "gut"
    elif median_error <= 35 and p90_error <= 80:
        quality_label = "mittel"
    else:
        quality_label = "schwach"

    return {
        "quality_label": quality_label,
        "p90_error_m": p90_error,
        "used_scans": int(len(route_estimates)),
    }


def clean_route_comparison(
    route_comparison: pd.DataFrame,
    *,
    min_aps: int = 4,
    max_rmse_m: float = 120.0,
    max_error_m: float = 100.0,
    max_jump_m: float = 80.0,
    large_time_gap_s: float = 90.0,
) -> pd.DataFrame:
    if route_comparison.empty:
        return pd.DataFrame(columns=ROUTE_QUALITY_COLUMNS)

    route = route_comparison.copy()
    route["timestamp"] = pd.to_datetime(route["timestamp"], errors="coerce")
    route = route.sort_values("timestamp").reset_index(drop=True)
    route["gps_jump_m"] = _calculate_route_jumps(route, "actual_latitude", "actual_longitude")
    route["wifi_jump_m"] = _calculate_route_jumps(route, "estimated_latitude", "estimated_longitude")
    route["time_gap_s"] = route["timestamp"].diff().dt.total_seconds().fillna(0)
    route["is_outlier"] = False
    route["outlier_reason"] = ""

    _append_outlier_reason(route, route["matched_access_points"] < min_aps, "too_few_aps")
    _append_outlier_reason(route, route["residual_rmse"] > max_rmse_m, "high_rmse")
    _append_outlier_reason(route, route["error_m"] > max_error_m, "high_error")
    _append_large_jump_reasons(route, max_jump_m=max_jump_m, large_time_gap_s=large_time_gap_s)

    route["is_outlier"] = route["outlier_reason"] != ""
    clean_route = route.loc[~route["is_outlier"]].copy()
    output_columns = _route_quality_output_columns(route_comparison)
    return clean_route.loc[:, output_columns].reset_index(drop=True)


def add_route_quality_flags(route_comparison: pd.DataFrame, **kwargs: object) -> pd.DataFrame:
    if route_comparison.empty:
        return pd.DataFrame(columns=ROUTE_QUALITY_COLUMNS)

    route = route_comparison.copy()
    route["timestamp"] = pd.to_datetime(route["timestamp"], errors="coerce")
    route = route.sort_values("timestamp").reset_index(drop=True)
    route["gps_jump_m"] = _calculate_route_jumps(route, "actual_latitude", "actual_longitude")
    route["wifi_jump_m"] = _calculate_route_jumps(route, "estimated_latitude", "estimated_longitude")
    route["time_gap_s"] = route["timestamp"].diff().dt.total_seconds().fillna(0)
    route["is_outlier"] = False
    route["outlier_reason"] = ""

    min_aps = int(kwargs.get("min_aps", 4))
    max_rmse_m = float(kwargs.get("max_rmse_m", 120.0))
    max_error_m = float(kwargs.get("max_error_m", 100.0))
    max_jump_m = float(kwargs.get("max_jump_m", 80.0))
    large_time_gap_s = float(kwargs.get("large_time_gap_s", 90.0))

    _append_outlier_reason(route, route["matched_access_points"] < min_aps, "too_few_aps")
    _append_outlier_reason(route, route["residual_rmse"] > max_rmse_m, "high_rmse")
    _append_outlier_reason(route, route["error_m"] > max_error_m, "high_error")
    _append_large_jump_reasons(route, max_jump_m=max_jump_m, large_time_gap_s=large_time_gap_s)

    route["is_outlier"] = route["outlier_reason"] != ""
    output_columns = _route_quality_output_columns(route_comparison)
    return route.loc[:, output_columns].reset_index(drop=True)


def save_route_estimates(route_estimates: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    route_estimates.to_csv(path, index=False)
    return path


def _route_quality_output_columns(route_comparison: pd.DataFrame) -> list[str]:
    return list(
        dict.fromkeys(
            list(route_comparison.columns)
            + [
                "gps_jump_m",
                "wifi_jump_m",
                "is_outlier",
                "outlier_reason",
            ]
        )
    )


def _snap_route_estimates_to_roads(
    route_estimates: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    max_snap_distance_m: float,
) -> pd.DataFrame:
    if route_estimates.empty:
        return route_estimates.copy()

    route = route_estimates.copy()
    for index, row in route.iterrows():
        raw_latitude = float(row["estimated_latitude"])
        raw_longitude = float(row["estimated_longitude"])
        snapped_position = snap_position_to_nearest_road(
            raw_latitude,
            raw_longitude,
            osm_map,
            max_snap_distance_m=max_snap_distance_m,
        )
        route.at[index, "raw_estimated_latitude"] = raw_latitude
        route.at[index, "raw_estimated_longitude"] = raw_longitude
        route.at[index, "estimated_latitude"] = snapped_position["latitude"]
        route.at[index, "estimated_longitude"] = snapped_position["longitude"]
        route.at[index, "snap_distance_m"] = snapped_position["snap_distance_m"]
        route.at[index, "error_m"] = calculate_distance_m(
            float(row["actual_latitude"]),
            float(row["actual_longitude"]),
            snapped_position["latitude"],
            snapped_position["longitude"],
            float(row["actual_latitude"]),
        )

    route["method"] = route["method"].astype(str) + "_road_snapped"
    return route.reset_index(drop=True)


def _calculate_route_jumps(route: pd.DataFrame, latitude_column: str, longitude_column: str) -> pd.Series:
    jumps = [0.0]
    for previous, current in zip(route.iloc[:-1].itertuples(index=False), route.iloc[1:].itertuples(index=False)):
        previous_latitude = float(getattr(previous, latitude_column))
        previous_longitude = float(getattr(previous, longitude_column))
        current_latitude = float(getattr(current, latitude_column))
        current_longitude = float(getattr(current, longitude_column))
        jumps.append(
            calculate_distance_m(
                previous_latitude,
                previous_longitude,
                current_latitude,
                current_longitude,
                (previous_latitude + current_latitude) / 2,
            )
        )
    return pd.Series(jumps, index=route.index)


def _append_outlier_reason(route: pd.DataFrame, mask: pd.Series, reason: str) -> None:
    route.loc[mask, "outlier_reason"] = route.loc[mask, "outlier_reason"].apply(
        lambda current: reason if current == "" else f"{current};{reason}"
    )


def _append_large_jump_reasons(route: pd.DataFrame, *, max_jump_m: float, large_time_gap_s: float) -> None:
    last_good_index: int | None = None

    for index, row in route.iterrows():
        if row["outlier_reason"] != "":
            continue

        if last_good_index is None:
            last_good_index = index
            continue

        previous = route.loc[last_good_index]
        time_gap_s = (row["timestamp"] - previous["timestamp"]).total_seconds()
        jump_m = calculate_distance_m(
            float(previous["estimated_latitude"]),
            float(previous["estimated_longitude"]),
            float(row["estimated_latitude"]),
            float(row["estimated_longitude"]),
            (float(previous["estimated_latitude"]) + float(row["estimated_latitude"])) / 2,
        )
        if jump_m > max_jump_m and time_gap_s <= large_time_gap_s:
            route.at[index, "outlier_reason"] = "large_jump"
            continue

        last_good_index = index


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


def _get_scan_position_from_reference(scan_rows: pd.DataFrame) -> dict[str, float] | None:
    if not {"latitude", "longitude"}.issubset(scan_rows.columns):
        return None
    if scan_rows["latitude"].isna().all() or scan_rows["longitude"].isna().all():
        return None
    return {
        "latitude": float(scan_rows["latitude"].iloc[0]),
        "longitude": float(scan_rows["longitude"].iloc[0]),
    }


def _build_scan_fingerprints(calibration_dataframe: pd.DataFrame) -> list[dict[str, object]]:
    fingerprints: list[dict[str, object]] = []
    for scan_id, scan_rows in calibration_dataframe.groupby("scan_id", sort=False):
        position = _get_scan_position_from_reference(scan_rows)
        if position is None:
            continue
        rssi_by_network = (
            scan_rows.groupby("network_id", as_index=False)
            .agg(rssi=("rssi", "mean"))
            .set_index("network_id")["rssi"]
            .to_dict()
        )
        fingerprints.append(
            {
                "scan_id": scan_id,
                "timestamp": scan_rows["timestamp"].iloc[0],
                "latitude": position["latitude"],
                "longitude": position["longitude"],
                "rssi_by_network": rssi_by_network,
            }
        )
    return fingerprints


def _estimate_scan_position_wknn_from_fingerprints(
    target_fingerprint: dict[str, object],
    reference_fingerprints: list[dict[str, object]],
    *,
    k: int,
    min_matches: int,
) -> dict[str, object] | None:
    input_by_network = target_fingerprint["rssi_by_network"]
    if not isinstance(input_by_network, dict) or not input_by_network:
        return None

    candidate_rows: list[dict[str, object]] = []
    for reference in reference_fingerprints:
        if reference["scan_id"] == target_fingerprint["scan_id"]:
            continue

        reference_by_network = reference["rssi_by_network"]
        if not isinstance(reference_by_network, dict):
            continue
        common_networks = set(input_by_network).intersection(reference_by_network)
        if len(common_networks) < min_matches:
            continue

        squared_distance = 0.0
        for network_id in common_networks:
            input_rssi = float(input_by_network[network_id])
            reference_rssi = float(reference_by_network[network_id])
            weight = 1.0 + max(input_rssi, reference_rssi, -90.0) + 90.0
            squared_distance += weight * (input_rssi - reference_rssi) ** 2

        mean_distance = (squared_distance / len(common_networks)) ** 0.5
        candidate_rows.append(
            {
                "latitude": float(reference["latitude"]),
                "longitude": float(reference["longitude"]),
                "rssi_distance": float(mean_distance),
                "matched_access_points": int(len(common_networks)),
            }
        )

    if not candidate_rows:
        return None

    candidates = (
        pd.DataFrame(candidate_rows)
        .sort_values(["rssi_distance", "matched_access_points"], ascending=[True, False])
        .head(k)
        .copy()
    )
    weights = 1.0 / (candidates["rssi_distance"].clip(lower=1.0) ** 2)
    return {
        "latitude": float((candidates["latitude"] * weights).sum() / weights.sum()),
        "longitude": float((candidates["longitude"] * weights).sum() / weights.sum()),
        "matched_access_points": int(candidates["matched_access_points"].max()),
        "residual_rmse": float(candidates["rssi_distance"].mean()),
        "method": "wknn_fingerprinting",
    }

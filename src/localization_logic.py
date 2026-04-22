import math
from pathlib import Path

import pandas as pd

LAT_METERS = 111_320
MIN_TRIANGULATION_SCANS = 3
DEFAULT_STEP_SEQUENCE = (20.0, 8.0, 3.0, 1.0)


def add_network_identifier(cleaned_dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = cleaned_dataframe.copy()
    dataframe["network_id"] = dataframe.apply(
        lambda row: build_network_id(row["ssid"], row["bssid"]),
        axis=1,
    )
    return dataframe


def build_network_id(ssid: str, bssid: str) -> str:
    return f"{ssid} | {bssid}"


def create_network_observations(
    cleaned_dataframe: pd.DataFrame,
    scan_positions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    dataframe = add_network_identifier(cleaned_dataframe)

    observations = (
        dataframe.groupby(
            ["network_id", "ssid", "bssid", "scan_id", "timestamp"],
            as_index=False,
        )
        .agg(
            channel=("channel", "first"),
            frequency=("frequency", "first"),
            mean_rssi=("rssi", "mean"),
            strongest_rssi=("rssi", "max"),
            observation_count=("rssi", "count"),
        )
        .sort_values(["network_id", "timestamp"])
        .reset_index(drop=True)
    )

    if scan_positions is not None:
        position_columns = ["scan_id", "latitude", "longitude", "matched_access_points", "residual_rmse", "confidence_score"]
        available_columns = [column for column in position_columns if column in scan_positions.columns]
        observations = observations.merge(
            scan_positions.loc[:, available_columns],
            on="scan_id",
            how="left",
        )
    elif {"latitude", "longitude"}.issubset(dataframe.columns):
        coordinates = (
            dataframe.groupby(["scan_id", "timestamp"], as_index=False)
            .agg(
                latitude=("latitude", "first"),
                longitude=("longitude", "first"),
                accuracy_m=("accuracy_m", "mean"),
            )
        )
        observations = observations.merge(
            coordinates,
            on=["scan_id", "timestamp"],
            how="left",
        )

    observations["estimated_radius_m"] = observations["mean_rssi"].apply(estimate_radius_from_rssi)
    return observations


def create_network_summary(network_observations: pd.DataFrame) -> pd.DataFrame:
    summary = (
        network_observations.groupby(["network_id", "ssid", "bssid"], as_index=False)
        .agg(
            scan_count=("scan_id", "nunique"),
            total_observations=("observation_count", "sum"),
            mean_rssi=("mean_rssi", "mean"),
            strongest_rssi=("strongest_rssi", "max"),
            min_radius_m=("estimated_radius_m", "min"),
            max_radius_m=("estimated_radius_m", "max"),
        )
        .sort_values(["scan_count", "total_observations", "mean_rssi"], ascending=[False, False, False])
        .reset_index(drop=True)
    )

    summary["overlap_point_count"] = 0
    return summary


def estimate_radius_from_rssi(
    rssi: float,
    reference_rssi: float = -45.0,
    path_loss_exponent: float = 3.0,
    min_radius_m: float = 3.0,
    max_radius_m: float = 80.0,
) -> float:
    distance = 10 ** ((reference_rssi - float(rssi)) / (10 * path_loss_exponent))
    return max(min_radius_m, min(max_radius_m, distance))


def triangulate_access_points(
    calibration_dataframe: pd.DataFrame,
    *,
    min_scans: int = MIN_TRIANGULATION_SCANS,
    allow_empty: bool = False,
) -> pd.DataFrame:
    if calibration_dataframe.empty:
        if allow_empty:
            return pd.DataFrame(columns=_access_point_columns())
        raise ValueError("Keine Kalibrierungsdaten fuer die AP-Triangulation vorhanden.")

    network_observations = create_network_observations(calibration_dataframe)
    network_frames: list[dict[str, object]] = []

    for (network_id, ssid, bssid), network_rows in network_observations.groupby(["network_id", "ssid", "bssid"]):
        scan_count = int(network_rows["scan_id"].nunique())
        if scan_count < min_scans:
            continue

        best_point = _estimate_point_from_circles(network_rows)
        if best_point is None:
            continue

        quality_flag = _classify_quality(scan_count, best_point["rmse_m"])
        network_frames.append(
            {
                "network_id": network_id,
                "ssid": ssid,
                "bssid": bssid,
                "latitude": best_point["latitude"],
                "longitude": best_point["longitude"],
                "scan_count": scan_count,
                "total_observations": int(network_rows["observation_count"].sum()),
                "mean_rssi": float(network_rows["mean_rssi"].mean()),
                "min_radius_m": float(network_rows["estimated_radius_m"].min()),
                "max_radius_m": float(network_rows["estimated_radius_m"].max()),
                "rmse_m": float(best_point["rmse_m"]),
                "quality_flag": quality_flag,
            }
        )

    if not network_frames:
        if allow_empty:
            return pd.DataFrame(columns=_access_point_columns())
        raise ValueError("Keine BSSIDs mit mindestens 3 eindeutigen Kalibrierungs-Scans gefunden.")

    return (
        pd.DataFrame(network_frames, columns=_access_point_columns())
        .sort_values(["quality_flag", "scan_count", "rmse_m", "network_id"], ascending=[True, False, True, True])
        .reset_index(drop=True)
    )


def triangulate_scan_positions(
    cleaned_dataframe: pd.DataFrame,
    access_points: pd.DataFrame,
    *,
    min_matches: int = MIN_TRIANGULATION_SCANS,
) -> pd.DataFrame:
    if cleaned_dataframe.empty or access_points.empty:
        return pd.DataFrame(columns=_scan_position_columns())

    scan_frames: list[dict[str, object]] = []

    for scan_id, scan_rows in cleaned_dataframe.groupby("scan_id"):
        input_observations = (
            scan_rows.groupby(["network_id", "ssid", "bssid"], as_index=False)
            .agg(rssi=("rssi", "mean"))
            .sort_values("network_id")
            .reset_index(drop=True)
        )
        estimate = estimate_position_from_access_points(
            access_points,
            input_observations,
            min_matches=min_matches,
        )
        if estimate is None:
            continue

        scan_frames.append(
            {
                "scan_id": scan_id,
                "timestamp": scan_rows["timestamp"].iloc[0],
                "latitude": estimate["latitude"],
                "longitude": estimate["longitude"],
                "matched_access_points": estimate["matched_networks"],
                "residual_rmse": estimate["residual_rmse"],
                "confidence_score": estimate["confidence_score"],
            }
        )

    if not scan_frames:
        return pd.DataFrame(columns=_scan_position_columns())

    return (
        pd.DataFrame(scan_frames, columns=_scan_position_columns())
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


def estimate_position_from_access_points(
    access_points: pd.DataFrame,
    input_observations: pd.DataFrame,
    *,
    min_matches: int = MIN_TRIANGULATION_SCANS,
) -> dict[str, object] | None:
    if input_observations.empty or access_points.empty:
        return None

    merged = (
        input_observations.groupby(["network_id", "ssid", "bssid"], as_index=False)
        .agg(rssi=("rssi", "mean"))
        .merge(
            access_points,
            on=["network_id", "ssid", "bssid"],
            how="inner",
            suffixes=("", "_ap"),
        )
    )
    if len(merged) < min_matches:
        return None

    merged = merged.copy()
    merged["estimated_radius_m"] = merged["rssi"].apply(estimate_radius_from_rssi)
    best_point = _estimate_point_from_circles(merged)
    if best_point is None:
        return None

    matched_access_points = merged.loc[
        :,
        [
            "ssid",
            "bssid",
            "rssi",
            "estimated_radius_m",
            "latitude",
            "longitude",
            "scan_count",
            "rmse_m",
            "quality_flag",
        ],
    ].copy()
    matched_access_points = matched_access_points.sort_values(
        ["quality_flag", "estimated_radius_m", "ssid", "bssid"]
    ).reset_index(drop=True)

    confidence_score = float(len(merged) / max(best_point["rmse_m"], 1.0))
    return {
        "latitude": float(best_point["latitude"]),
        "longitude": float(best_point["longitude"]),
        "matched_networks": int(len(merged)),
        "residual_rmse": float(best_point["rmse_m"]),
        "confidence_score": confidence_score,
        "matched_access_points": matched_access_points,
        "actual_latitude": None,
        "actual_longitude": None,
        "error_m": None,
    }


def filter_network_observations(
    network_observations: pd.DataFrame,
    network_id: str,
) -> pd.DataFrame:
    return network_observations.loc[network_observations["network_id"] == network_id].copy()


def estimate_overlap_points(
    network_observations: pd.DataFrame,
    step_m: float = 2.5,
) -> pd.DataFrame:
    valid_observations = network_observations.dropna(subset=["latitude", "longitude"]).copy()
    if len(valid_observations) < 2:
        return pd.DataFrame(columns=["latitude", "longitude", "support_count"])

    mean_lat = float(valid_observations["latitude"].mean())
    lat_step = step_m / LAT_METERS
    lon_step = step_m / (LAT_METERS * max(0.1, math.cos(math.radians(mean_lat))))

    min_lat = float((valid_observations["latitude"] - valid_observations["estimated_radius_m"] / LAT_METERS).min())
    max_lat = float((valid_observations["latitude"] + valid_observations["estimated_radius_m"] / LAT_METERS).max())
    min_lon = float(
        (
            valid_observations["longitude"]
            - valid_observations["estimated_radius_m"] / (LAT_METERS * max(0.1, math.cos(math.radians(mean_lat))))
        ).min()
    )
    max_lon = float(
        (
            valid_observations["longitude"]
            + valid_observations["estimated_radius_m"] / (LAT_METERS * max(0.1, math.cos(math.radians(mean_lat))))
        ).max()
    )

    overlap_points: list[dict[str, float]] = []
    max_support = 0
    latitude = min_lat

    while latitude <= max_lat:
        longitude = min_lon
        while longitude <= max_lon:
            support_count = count_covering_circles(latitude, longitude, valid_observations, mean_lat)
            if support_count >= 2:
                if support_count > max_support:
                    overlap_points = []
                    max_support = support_count
                if support_count == max_support:
                    overlap_points.append(
                        {
                            "latitude": latitude,
                            "longitude": longitude,
                            "support_count": support_count,
                        }
                    )
            longitude += lon_step
        latitude += lat_step

    return pd.DataFrame(overlap_points)


def count_covering_circles(
    latitude: float,
    longitude: float,
    network_observations: pd.DataFrame,
    mean_latitude: float,
) -> int:
    support_count = 0

    for _, row in network_observations.iterrows():
        distance = calculate_distance_m(
            latitude,
            longitude,
            float(row["latitude"]),
            float(row["longitude"]),
            mean_latitude,
        )
        if distance <= float(row["estimated_radius_m"]):
            support_count += 1

    return support_count


def calculate_distance_m(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
    mean_latitude: float,
) -> float:
    lat_distance = (latitude_2 - latitude_1) * LAT_METERS
    lon_distance = (
        (longitude_2 - longitude_1)
        * LAT_METERS
        * max(0.1, math.cos(math.radians(mean_latitude)))
    )
    return math.sqrt(lat_distance**2 + lon_distance**2)


def save_network_observations(
    network_observations: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    network_observations.to_csv(path, index=False)
    return path


def save_network_summary(
    network_summary: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    network_summary.to_csv(path, index=False)
    return path


def save_triangulated_access_points(
    access_points: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    access_points.to_csv(path, index=False)
    return path


def save_triangulated_scan_positions(
    scan_positions: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    scan_positions.to_csv(path, index=False)
    return path


def _estimate_point_from_circles(
    observations: pd.DataFrame,
    *,
    latitude_column: str = "latitude",
    longitude_column: str = "longitude",
    radius_column: str = "estimated_radius_m",
    step_sequence: tuple[float, ...] = DEFAULT_STEP_SEQUENCE,
) -> dict[str, float] | None:
    valid = observations.dropna(subset=[latitude_column, longitude_column, radius_column]).copy()
    if valid.empty:
        return None

    centroid_lat, centroid_lon = _weighted_centroid(
        valid,
        latitude_column=latitude_column,
        longitude_column=longitude_column,
        radius_column=radius_column,
    )
    search_radius_m = _compute_search_radius(
        valid,
        centroid_lat,
        centroid_lon,
        latitude_column=latitude_column,
        longitude_column=longitude_column,
        radius_column=radius_column,
    )

    best_lat = centroid_lat
    best_lon = centroid_lon
    best_rmse = _circle_residual_rmse(
        best_lat,
        best_lon,
        valid,
        latitude_column=latitude_column,
        longitude_column=longitude_column,
        radius_column=radius_column,
    )

    for index, step_m in enumerate(step_sequence):
        search_extent_m = search_radius_m if index == 0 else max(step_sequence[index - 1] * 2.0, step_m * 3.0)
        candidate = _search_grid(
            valid,
            center_latitude=best_lat,
            center_longitude=best_lon,
            search_extent_m=search_extent_m,
            step_m=step_m,
            latitude_column=latitude_column,
            longitude_column=longitude_column,
            radius_column=radius_column,
        )
        if candidate["rmse_m"] < best_rmse:
            best_lat = candidate["latitude"]
            best_lon = candidate["longitude"]
            best_rmse = candidate["rmse_m"]

    return {"latitude": best_lat, "longitude": best_lon, "rmse_m": best_rmse}


def _search_grid(
    observations: pd.DataFrame,
    *,
    center_latitude: float,
    center_longitude: float,
    search_extent_m: float,
    step_m: float,
    latitude_column: str,
    longitude_column: str,
    radius_column: str,
) -> dict[str, float]:
    mean_latitude = float((observations[latitude_column].mean() + center_latitude) / 2)
    lat_step = step_m / LAT_METERS
    lon_scale = LAT_METERS * max(0.1, math.cos(math.radians(mean_latitude)))
    lon_step = step_m / lon_scale
    lat_radius = search_extent_m / LAT_METERS
    lon_radius = search_extent_m / lon_scale

    best_latitude = center_latitude
    best_longitude = center_longitude
    best_rmse = math.inf

    latitude = center_latitude - lat_radius
    while latitude <= center_latitude + lat_radius + (lat_step / 2):
        longitude = center_longitude - lon_radius
        while longitude <= center_longitude + lon_radius + (lon_step / 2):
            rmse_m = _circle_residual_rmse(
                latitude,
                longitude,
                observations,
                latitude_column=latitude_column,
                longitude_column=longitude_column,
                radius_column=radius_column,
            )
            if rmse_m < best_rmse:
                best_latitude = latitude
                best_longitude = longitude
                best_rmse = rmse_m
            longitude += lon_step
        latitude += lat_step

    return {"latitude": best_latitude, "longitude": best_longitude, "rmse_m": best_rmse}


def _circle_residual_rmse(
    latitude: float,
    longitude: float,
    observations: pd.DataFrame,
    *,
    latitude_column: str,
    longitude_column: str,
    radius_column: str,
) -> float:
    residuals: list[float] = []
    mean_latitude = float((observations[latitude_column].mean() + latitude) / 2)

    for row in observations.itertuples(index=False):
        row_latitude = getattr(row, latitude_column)
        row_longitude = getattr(row, longitude_column)
        row_radius = getattr(row, radius_column)
        distance = calculate_distance_m(
            latitude,
            longitude,
            float(row_latitude),
            float(row_longitude),
            mean_latitude,
        )
        residuals.append(distance - float(row_radius))

    squared_error = sum(residual**2 for residual in residuals) / len(residuals)
    return float(math.sqrt(squared_error))


def _weighted_centroid(
    observations: pd.DataFrame,
    *,
    latitude_column: str,
    longitude_column: str,
    radius_column: str,
) -> tuple[float, float]:
    weights = 1.0 / observations[radius_column].clip(lower=1.0)
    latitude = float((observations[latitude_column] * weights).sum() / weights.sum())
    longitude = float((observations[longitude_column] * weights).sum() / weights.sum())
    return latitude, longitude


def _compute_search_radius(
    observations: pd.DataFrame,
    centroid_latitude: float,
    centroid_longitude: float,
    *,
    latitude_column: str,
    longitude_column: str,
    radius_column: str,
) -> float:
    max_extent = 0.0
    mean_latitude = float((observations[latitude_column].mean() + centroid_latitude) / 2)
    for row in observations.itertuples(index=False):
        row_latitude = getattr(row, latitude_column)
        row_longitude = getattr(row, longitude_column)
        row_radius = getattr(row, radius_column)
        extent = calculate_distance_m(
            centroid_latitude,
            centroid_longitude,
            float(row_latitude),
            float(row_longitude),
            mean_latitude,
        ) + float(row_radius)
        max_extent = max(max_extent, extent)

    return max(max_extent, 12.0)


def _classify_quality(scan_count: int, rmse_m: float) -> str:
    if scan_count >= 5 and rmse_m <= 12.0:
        return "good"
    if scan_count >= 4 and rmse_m <= 25.0:
        return "usable"
    return "weak"


def _access_point_columns() -> list[str]:
    return [
        "network_id",
        "ssid",
        "bssid",
        "latitude",
        "longitude",
        "scan_count",
        "total_observations",
        "mean_rssi",
        "min_radius_m",
        "max_radius_m",
        "rmse_m",
        "quality_flag",
    ]


def _scan_position_columns() -> list[str]:
    return [
        "scan_id",
        "timestamp",
        "latitude",
        "longitude",
        "matched_access_points",
        "residual_rmse",
        "confidence_score",
    ]

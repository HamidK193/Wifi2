import pandas as pd

from src.localization_logic import (
    calculate_distance_m,
    estimate_position_from_access_points,
    triangulate_access_points,
)


def get_scan_input_observations(cleaned_dataframe: pd.DataFrame, scan_id: str) -> pd.DataFrame:
    scan_rows = cleaned_dataframe.loc[cleaned_dataframe["scan_id"] == scan_id].copy()
    if scan_rows.empty:
        return pd.DataFrame(columns=["network_id", "ssid", "bssid", "rssi"])

    return (
        scan_rows.groupby(["network_id", "ssid", "bssid"], as_index=False)
        .agg(rssi=("rssi", "mean"))
        .sort_values("network_id")
        .reset_index(drop=True)
    )


def parse_manual_wifi_input(text: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("ssid"):
            continue

        separator = ";" if ";" in line else ","
        parts = [part.strip() for part in line.split(separator)]
        if len(parts) != 3:
            continue

        ssid, bssid, rssi_text = parts
        try:
            rssi = float(rssi_text)
        except ValueError:
            continue

        rows.append(
            {
                "network_id": f"{ssid} | {bssid}",
                "ssid": ssid,
                "bssid": bssid,
                "rssi": rssi,
            }
        )

    return pd.DataFrame(rows, columns=["network_id", "ssid", "bssid", "rssi"])


def run_leave_one_scan_out_benchmark(
    calibration_dataframe: pd.DataFrame,
    scan_id: str,
    *,
    min_matches: int = 3,
) -> dict[str, object] | None:
    input_observations = get_scan_input_observations(calibration_dataframe, scan_id)
    if input_observations.empty:
        return None

    reference = calibration_dataframe.loc[calibration_dataframe["scan_id"] != scan_id].copy()
    access_points = triangulate_access_points(reference, min_scans=min_matches, allow_empty=True)
    if access_points.empty:
        return None

    estimate = estimate_position_from_access_points(
        access_points,
        input_observations,
        min_matches=min_matches,
    )
    if estimate is None:
        return None

    actual_position = get_scan_position(calibration_dataframe, scan_id)
    if actual_position is not None:
        estimate["actual_latitude"] = actual_position["latitude"]
        estimate["actual_longitude"] = actual_position["longitude"]
        estimate["error_m"] = calculate_distance_m(
            estimate["latitude"],
            estimate["longitude"],
            actual_position["latitude"],
            actual_position["longitude"],
            actual_position["latitude"],
        )

    estimate["input_observations"] = input_observations
    estimate["benchmark_access_points"] = access_points
    return estimate


def estimate_position_from_fingerprint(
    cleaned_dataframe: pd.DataFrame,
    input_observations: pd.DataFrame,
    *,
    exclude_scan_id: str | None = None,
    min_matches: int = 3,
) -> dict[str, object] | None:
    reference = cleaned_dataframe.copy()
    if exclude_scan_id is not None:
        reference = reference.loc[reference["scan_id"] != exclude_scan_id].copy()

    access_points = triangulate_access_points(reference, min_scans=min_matches, allow_empty=True)
    if access_points.empty:
        return None

    estimate = estimate_position_from_access_points(
        access_points,
        input_observations,
        min_matches=min_matches,
    )
    if estimate is None or exclude_scan_id is None:
        return estimate

    actual_position = get_scan_position(cleaned_dataframe, exclude_scan_id)
    if actual_position is not None:
        estimate["actual_latitude"] = actual_position["latitude"]
        estimate["actual_longitude"] = actual_position["longitude"]
        estimate["error_m"] = calculate_distance_m(
            estimate["latitude"],
            estimate["longitude"],
            actual_position["latitude"],
            actual_position["longitude"],
            actual_position["latitude"],
        )

    return estimate


def estimate_route_positions(
    cleaned_dataframe: pd.DataFrame,
    scan_summary: pd.DataFrame,
    *,
    k: int = 3,
    min_matches: int = 1,
) -> pd.DataFrame:
    _ = k
    rows: list[dict[str, object]] = []

    for scan_id in scan_summary["scan_id"].tolist():
        input_observations = get_scan_input_observations(cleaned_dataframe, scan_id)
        estimate = estimate_position_from_fingerprint(
            cleaned_dataframe,
            input_observations,
            exclude_scan_id=scan_id,
            min_matches=min_matches,
        )
        if estimate is None:
            continue

        rows.append(
            {
                "scan_id": scan_id,
                "actual_latitude": estimate["actual_latitude"],
                "actual_longitude": estimate["actual_longitude"],
                "estimated_latitude": estimate["latitude"],
                "estimated_longitude": estimate["longitude"],
                "matched_networks": estimate["matched_networks"],
                "best_rmse": estimate.get("best_rmse", estimate.get("residual_rmse")),
                "error_m": estimate["error_m"],
            }
        )

    return pd.DataFrame(rows)


def get_scan_position(cleaned_dataframe: pd.DataFrame, scan_id: str) -> dict[str, float] | None:
    if not {"latitude", "longitude"}.issubset(cleaned_dataframe.columns):
        return None

    scan_rows = cleaned_dataframe.loc[cleaned_dataframe["scan_id"] == scan_id]
    if scan_rows.empty:
        return None

    if scan_rows["latitude"].isna().all() or scan_rows["longitude"].isna().all():
        return None

    return {
        "latitude": float(scan_rows["latitude"].iloc[0]),
        "longitude": float(scan_rows["longitude"].iloc[0]),
    }

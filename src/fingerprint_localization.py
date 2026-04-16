import pandas as pd

from src.localization_logic import build_network_id, calculate_distance_m


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
                "network_id": build_network_id(ssid, bssid),
                "ssid": ssid,
                "bssid": bssid,
                "rssi": rssi,
            }
        )

    return pd.DataFrame(rows, columns=["network_id", "ssid", "bssid", "rssi"])


def estimate_position_from_fingerprint(
    cleaned_dataframe: pd.DataFrame,
    input_observations: pd.DataFrame,
    *,
    exclude_scan_id: str | None = None,
    k: int = 3,
    min_matches: int = 1,
) -> dict[str, object] | None:
    if input_observations.empty:
        return None

    reference = cleaned_dataframe.copy()
    if exclude_scan_id is not None:
        reference = reference.loc[reference["scan_id"] != exclude_scan_id].copy()

    input_by_network = (
        input_observations.groupby("network_id", as_index=True)["rssi"]
        .mean()
        .dropna()
    )
    if input_by_network.empty:
        return None

    scan_positions = (
        reference.groupby("scan_id", as_index=False)
        .agg(latitude=("latitude", "first"), longitude=("longitude", "first"))
    )
    reference_rssi = reference.pivot_table(
        index="scan_id",
        columns="network_id",
        values="rssi",
        aggfunc="mean",
    )

    common_networks = [network_id for network_id in input_by_network.index if network_id in reference_rssi.columns]
    if not common_networks:
        return None

    candidates: list[dict[str, object]] = []

    for scan_id, reference_row in reference_rssi[common_networks].iterrows():
        available = reference_row.dropna()
        if len(available) < min_matches:
            continue

        input_values = input_by_network.loc[available.index]
        rmse = float(((available - input_values) ** 2).mean() ** 0.5)
        matched_networks = int(len(available))
        candidates.append(
            {
                "scan_id": scan_id,
                "rmse": rmse,
                "matched_networks": matched_networks,
                "weight": matched_networks / max(rmse, 1.0),
            }
        )

    if not candidates:
        return None

    candidates_dataframe = (
        pd.DataFrame(candidates)
        .merge(scan_positions, on="scan_id", how="left")
        .sort_values(["rmse", "matched_networks"], ascending=[True, False])
        .head(k)
        .reset_index(drop=True)
    )

    weight_sum = float(candidates_dataframe["weight"].sum())
    latitude = float((candidates_dataframe["latitude"] * candidates_dataframe["weight"]).sum() / weight_sum)
    longitude = float((candidates_dataframe["longitude"] * candidates_dataframe["weight"]).sum() / weight_sum)

    estimate: dict[str, object] = {
        "latitude": latitude,
        "longitude": longitude,
        "matched_networks": int(candidates_dataframe["matched_networks"].max()),
        "best_rmse": float(candidates_dataframe["rmse"].min()),
        "candidates": candidates_dataframe,
        "actual_latitude": None,
        "actual_longitude": None,
        "error_m": None,
    }

    if exclude_scan_id is not None:
        actual_position = get_scan_position(cleaned_dataframe, exclude_scan_id)
        if actual_position is not None:
            estimate["actual_latitude"] = actual_position["latitude"]
            estimate["actual_longitude"] = actual_position["longitude"]
            estimate["error_m"] = calculate_distance_m(
                latitude,
                longitude,
                actual_position["latitude"],
                actual_position["longitude"],
                actual_position["latitude"],
            )

    return estimate


def get_scan_position(cleaned_dataframe: pd.DataFrame, scan_id: str) -> dict[str, float] | None:
    scan_rows = cleaned_dataframe.loc[cleaned_dataframe["scan_id"] == scan_id]
    if scan_rows.empty:
        return None

    return {
        "latitude": float(scan_rows["latitude"].iloc[0]),
        "longitude": float(scan_rows["longitude"].iloc[0]),
    }

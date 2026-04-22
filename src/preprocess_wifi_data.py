from math import cos, radians
from pathlib import Path

import pandas as pd

from src.localization_logic import build_network_id

MIN_VALID_TIMESTAMP = pd.Timestamp("2020-01-01")
BASE_COLUMN_MAPPING = {
    "MAC": "bssid",
    "SSID": "ssid",
    "FirstSeen": "timestamp",
    "Channel": "channel",
    "Frequency": "frequency",
    "RSSI": "rssi",
}
COORDINATE_COLUMN_MAPPING = {
    "CurrentLatitude": "latitude",
    "CurrentLongitude": "longitude",
    "AccuracyMeters": "accuracy_m",
}

BASE_OUTPUT_COLUMNS = [
    "scan_id",
    "network_id",
    "timestamp",
    "bssid",
    "ssid",
    "channel",
    "frequency",
    "rssi",
]
COORDINATE_OUTPUT_COLUMNS = ["latitude", "longitude", "accuracy_m"]


def clean_wifi_data(
    dataframe: pd.DataFrame,
    *,
    require_coordinates: bool = False,
    include_coordinates: bool = True,
) -> pd.DataFrame:
    required_columns = list(BASE_COLUMN_MAPPING)
    if require_coordinates:
        required_columns.extend(COORDINATE_COLUMN_MAPPING)

    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Fehlende Pflichtspalten: {missing_text}")

    filtered = dataframe.copy()
    if "Type" in filtered.columns:
        filtered = filtered.loc[filtered["Type"] == "WIFI"].copy()

    selected_columns = list(BASE_COLUMN_MAPPING)
    for column_name in COORDINATE_COLUMN_MAPPING:
        if column_name in filtered.columns:
            selected_columns.append(column_name)

    cleaned = filtered.loc[:, selected_columns].rename(
        columns={**BASE_COLUMN_MAPPING, **COORDINATE_COLUMN_MAPPING}
    ).copy()

    for coordinate_column in COORDINATE_OUTPUT_COLUMNS:
        if coordinate_column not in cleaned.columns:
            cleaned[coordinate_column] = pd.NA

    cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")
    cleaned = cleaned.loc[cleaned["timestamp"] >= MIN_VALID_TIMESTAMP].copy()

    for column_name in ["channel", "frequency", "rssi", *COORDINATE_OUTPUT_COLUMNS]:
        cleaned[column_name] = pd.to_numeric(cleaned[column_name], errors="coerce")

    required_non_null_columns = ["bssid", "ssid", "timestamp", "rssi"]
    if require_coordinates:
        required_non_null_columns.extend(["latitude", "longitude"])

    cleaned = cleaned.dropna(subset=required_non_null_columns).copy()
    cleaned = cleaned.drop_duplicates(
        subset=["timestamp", "bssid", "ssid", "rssi", "latitude", "longitude"]
    ).copy()
    cleaned = cleaned.sort_values(["timestamp", "bssid"]).reset_index(drop=True)

    timestamp_index = {
        timestamp: index
        for index, timestamp in enumerate(cleaned["timestamp"].drop_duplicates(), start=1)
    }
    cleaned["scan_id"] = cleaned["timestamp"].map(timestamp_index).map(lambda index: f"scan_{index:02d}")
    cleaned["network_id"] = cleaned.apply(
        lambda row: build_network_id(row["ssid"], row["bssid"]),
        axis=1,
    )

    output_columns = BASE_OUTPUT_COLUMNS + COORDINATE_OUTPUT_COLUMNS if include_coordinates else BASE_OUTPUT_COLUMNS
    return cleaned.loc[:, output_columns]


def create_scan_summary(
    cleaned_dataframe: pd.DataFrame,
    scan_positions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    scan_summary = (
        cleaned_dataframe.groupby(["scan_id", "timestamp"], as_index=False)
        .agg(
            visible_networks=("bssid", "count"),
            unique_ssids=("ssid", "nunique"),
            mean_rssi=("rssi", "mean"),
            strongest_rssi=("rssi", "max"),
        )
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    if scan_positions is not None:
        position_columns = [column for column in scan_positions.columns if column != "timestamp"]
        return (
            scan_summary.merge(scan_positions.loc[:, position_columns], on="scan_id", how="left")
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

    if {"latitude", "longitude"}.issubset(cleaned_dataframe.columns):
        scan_positions_from_dataframe = (
            cleaned_dataframe.groupby(["scan_id", "timestamp"], as_index=False)
            .agg(
                latitude=("latitude", "first"),
                longitude=("longitude", "first"),
                accuracy_m=("accuracy_m", "mean"),
            )
        )
        return (
            scan_summary.merge(scan_positions_from_dataframe, on=["scan_id", "timestamp"], how="left")
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

    return scan_summary


def summarize_dataset(
    cleaned_dataframe: pd.DataFrame,
    scan_summary: pd.DataFrame,
) -> dict[str, object]:
    summary = {
        "rows": int(len(cleaned_dataframe)),
        "scans": int(scan_summary["scan_id"].nunique()),
        "unique_network_entities": int(cleaned_dataframe["network_id"].nunique()),
        "unique_bssids": int(cleaned_dataframe["bssid"].nunique()),
        "unique_ssids": int(cleaned_dataframe["ssid"].nunique()),
        "time_start": str(cleaned_dataframe["timestamp"].min()),
        "time_end": str(cleaned_dataframe["timestamp"].max()),
        "rssi_range": f"{int(cleaned_dataframe['rssi'].min())} bis {int(cleaned_dataframe['rssi'].max())} dBm",
    }

    if {"latitude", "longitude"}.issubset(scan_summary.columns):
        valid_positions = scan_summary.dropna(subset=["latitude", "longitude"]).copy()
        if not valid_positions.empty:
            latitudes = valid_positions["latitude"]
            longitudes = valid_positions["longitude"]

            lat_span_m = (latitudes.max() - latitudes.min()) * 111320
            mean_latitude = (latitudes.max() + latitudes.min()) / 2
            lon_span_m = (longitudes.max() - longitudes.min()) * 111320 * cos(radians(mean_latitude))

            summary["latitude_range"] = f"{latitudes.min():.6f} bis {latitudes.max():.6f}"
            summary["longitude_range"] = f"{longitudes.min():.6f} bis {longitudes.max():.6f}"
            summary["bbox_meters"] = f"{lat_span_m:.1f} m x {lon_span_m:.1f} m"
            return summary

    summary["latitude_range"] = "nicht verfuegbar"
    summary["longitude_range"] = "nicht verfuegbar"
    summary["bbox_meters"] = "nicht verfuegbar"
    return summary


def save_cleaned_data(cleaned_dataframe: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    cleaned_dataframe.to_csv(path, index=False)
    return path


def save_scan_summary(scan_summary: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    scan_summary.to_csv(path, index=False)
    return path


def save_dataset_summary(summary: dict[str, object], output_path: str | Path) -> Path:
    path = Path(output_path)

    with path.open("w", encoding="utf-8") as file:
        file.write("Datensatz-Zusammenfassung\n")
        file.write("=========================\n\n")
        for key, value in summary.items():
            file.write(f"{key}: {value}\n")

    return path

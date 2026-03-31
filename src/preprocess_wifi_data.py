from math import cos, radians
from pathlib import Path

import pandas as pd

COLUMN_MAPPING = {
    "MAC": "bssid",
    "SSID": "ssid",
    "FirstSeen": "timestamp",
    "Channel": "channel",
    "Frequency": "frequency",
    "RSSI": "rssi",
    "CurrentLatitude": "latitude",
    "CurrentLongitude": "longitude",
    "AccuracyMeters": "accuracy_m",
}

OUTPUT_COLUMNS = [
    "scan_id",
    "timestamp",
    "bssid",
    "ssid",
    "channel",
    "frequency",
    "rssi",
    "latitude",
    "longitude",
    "accuracy_m",
]


def clean_wifi_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [column for column in COLUMN_MAPPING if column not in dataframe.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Fehlende Pflichtspalten: {missing_text}")

    cleaned = dataframe.loc[:, COLUMN_MAPPING.keys()].rename(columns=COLUMN_MAPPING).copy()

    cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")

    for column_name in ["channel", "frequency", "rssi", "latitude", "longitude", "accuracy_m"]:
        cleaned[column_name] = pd.to_numeric(cleaned[column_name], errors="coerce")

    cleaned = cleaned.dropna(
        subset=["bssid", "ssid", "timestamp", "rssi", "latitude", "longitude"]
    ).copy()
    cleaned = cleaned.drop_duplicates(
        subset=["timestamp", "bssid", "ssid", "rssi", "latitude", "longitude"]
    ).copy()
    cleaned = cleaned.sort_values(["timestamp", "bssid"]).reset_index(drop=True)

    timestamp_index = {
        timestamp: index
        for index, timestamp in enumerate(cleaned["timestamp"].drop_duplicates(), start=1)
    }
    cleaned["scan_id"] = cleaned["timestamp"].map(timestamp_index).map(lambda index: f"scan_{index:02d}")

    return cleaned.loc[:, OUTPUT_COLUMNS]


def create_scan_summary(cleaned_dataframe: pd.DataFrame) -> pd.DataFrame:
    scan_summary = (
        cleaned_dataframe.groupby(["scan_id", "timestamp"], as_index=False)
        .agg(
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            accuracy_m=("accuracy_m", "mean"),
            visible_networks=("bssid", "count"),
            unique_ssids=("ssid", "nunique"),
            mean_rssi=("rssi", "mean"),
            strongest_rssi=("rssi", "max"),
        )
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    return scan_summary


def summarize_dataset(
    cleaned_dataframe: pd.DataFrame,
    scan_summary: pd.DataFrame,
) -> dict[str, object]:
    latitudes = scan_summary["latitude"]
    longitudes = scan_summary["longitude"]

    lat_span_m = (latitudes.max() - latitudes.min()) * 111320
    mean_latitude = (latitudes.max() + latitudes.min()) / 2
    lon_span_m = (longitudes.max() - longitudes.min()) * 111320 * cos(radians(mean_latitude))

    return {
        "rows": int(len(cleaned_dataframe)),
        "scans": int(scan_summary["scan_id"].nunique()),
        "unique_bssids": int(cleaned_dataframe["bssid"].nunique()),
        "unique_ssids": int(cleaned_dataframe["ssid"].nunique()),
        "time_start": str(cleaned_dataframe["timestamp"].min()),
        "time_end": str(cleaned_dataframe["timestamp"].max()),
        "rssi_range": f"{int(cleaned_dataframe['rssi'].min())} bis {int(cleaned_dataframe['rssi'].max())} dBm",
        "latitude_range": f"{cleaned_dataframe['latitude'].min():.6f} bis {cleaned_dataframe['latitude'].max():.6f}",
        "longitude_range": f"{cleaned_dataframe['longitude'].min():.6f} bis {cleaned_dataframe['longitude'].max():.6f}",
        "bbox_meters": f"{lat_span_m:.1f} m x {lon_span_m:.1f} m",
    }


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

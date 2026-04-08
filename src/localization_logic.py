import math
from pathlib import Path

import pandas as pd

LAT_METERS = 111_320


def add_network_identifier(cleaned_dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = cleaned_dataframe.copy()
    dataframe["network_id"] = dataframe.apply(
        lambda row: build_network_id(row["ssid"], row["bssid"]),
        axis=1,
    )
    return dataframe


def build_network_id(ssid: str, bssid: str) -> str:
    return f"{ssid} | {bssid}"


def create_network_observations(cleaned_dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = add_network_identifier(cleaned_dataframe)

    observations = (
        dataframe.groupby(
            ["network_id", "ssid", "bssid", "scan_id", "timestamp"],
            as_index=False,
        )
        .agg(
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            accuracy_m=("accuracy_m", "mean"),
            channel=("channel", "first"),
            frequency=("frequency", "first"),
            mean_rssi=("rssi", "mean"),
            strongest_rssi=("rssi", "max"),
            observation_count=("rssi", "count"),
        )
        .sort_values(["network_id", "timestamp"])
        .reset_index(drop=True)
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

    # Die teure Ueberlappungsberechnung erfolgt erst in der App fuer die
    # aktuelle Auswahl. So bleibt die Datenpipeline auch mit grossen Datensaetzen
    # schnell genug.
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


def filter_network_observations(
    network_observations: pd.DataFrame,
    network_id: str,
) -> pd.DataFrame:
    return network_observations.loc[network_observations["network_id"] == network_id].copy()


def estimate_overlap_points(
    network_observations: pd.DataFrame,
    step_m: float = 2.5,
) -> pd.DataFrame:
    if len(network_observations) < 2:
        return pd.DataFrame(columns=["latitude", "longitude", "support_count"])

    mean_lat = float(network_observations["latitude"].mean())
    lat_step = step_m / LAT_METERS
    lon_step = step_m / (LAT_METERS * max(0.1, math.cos(math.radians(mean_lat))))

    min_lat = float((network_observations["latitude"] - network_observations["estimated_radius_m"] / LAT_METERS).min())
    max_lat = float((network_observations["latitude"] + network_observations["estimated_radius_m"] / LAT_METERS).max())
    min_lon = float(
        (
            network_observations["longitude"]
            - network_observations["estimated_radius_m"] / (LAT_METERS * max(0.1, math.cos(math.radians(mean_lat))))
        ).min()
    )
    max_lon = float(
        (
            network_observations["longitude"]
            + network_observations["estimated_radius_m"] / (LAT_METERS * max(0.1, math.cos(math.radians(mean_lat))))
        ).max()
    )

    overlap_points: list[dict[str, float]] = []
    max_support = 0
    latitude = min_lat

    while latitude <= max_lat:
        longitude = min_lon
        while longitude <= max_lon:
            support_count = count_covering_circles(latitude, longitude, network_observations, mean_lat)
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

from math import cos, log10, radians, sqrt
from pathlib import Path

import pandas as pd
import pytest

from src.load_wifi_csv import load_wifi_csv

LAT_METERS = 111_320
REFERENCE_RSSI = -45.0
PATH_LOSS_EXPONENT = 3.0


def _distance_m(latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float) -> float:
    mean_latitude = (latitude_1 + latitude_2) / 2
    lat_distance = (latitude_2 - latitude_1) * LAT_METERS
    lon_distance = (longitude_2 - longitude_1) * LAT_METERS * max(0.1, cos(radians(mean_latitude)))
    return sqrt(lat_distance**2 + lon_distance**2)


def _rssi_from_distance(distance_m: float) -> int:
    bounded_distance = max(distance_m, 1.0)
    rssi = REFERENCE_RSSI - 10 * PATH_LOSS_EXPONENT * log10(bounded_distance)
    return int(round(rssi))


def _build_triangulation_dataframe() -> pd.DataFrame:
    access_points = [
        ("aa:aa:aa:aa:aa:01", "Alpha", 48.880200, 8.700200),
        ("bb:bb:bb:bb:bb:02", "Beta", 48.880260, 8.700480),
        ("cc:cc:cc:cc:cc:03", "Gamma", 48.879980, 8.700340),
    ]
    scan_positions = [
        ("2026-04-08 11:32:44", 48.880060, 8.700050),
        ("2026-04-08 11:32:54", 48.880340, 8.700120),
        ("2026-04-08 11:33:04", 48.880100, 8.700580),
        ("2026-04-08 11:33:14", 48.879920, 8.700260),
    ]

    rows: list[dict[str, object]] = []
    for timestamp, scan_latitude, scan_longitude in scan_positions:
        for mac, ssid, ap_latitude, ap_longitude in access_points:
            distance_m = _distance_m(scan_latitude, scan_longitude, ap_latitude, ap_longitude)
            rows.append(
                {
                    "MAC": mac,
                    "SSID": ssid,
                    "AuthMode": "WPA2",
                    "FirstSeen": timestamp,
                    "Channel": 6,
                    "Frequency": 2437,
                    "RSSI": _rssi_from_distance(distance_m),
                    "CurrentLatitude": scan_latitude,
                    "CurrentLongitude": scan_longitude,
                    "AltitudeMeters": 400.0,
                    "AccuracyMeters": 5.0,
                    "RCOIs": "",
                    "MfgrId": "",
                    "Type": "WIFI",
                }
            )

    rows.append(
        {
            "MAC": "dd:dd:dd:dd:dd:04",
            "SSID": "Beacon",
            "AuthMode": "Open",
            "FirstSeen": "2026-04-08 11:32:44",
            "Channel": "",
            "Frequency": 7936,
            "RSSI": -90,
            "CurrentLatitude": 48.880060,
            "CurrentLongitude": 8.700050,
            "AltitudeMeters": 400.0,
            "AccuracyMeters": 5.0,
            "RCOIs": "",
            "MfgrId": "",
            "Type": "BLE",
        }
    )

    return pd.DataFrame(rows)


@pytest.fixture
def sample_wigle_csv(tmp_path: Path) -> Path:
    csv_content = """WigleWifi-1.6,appRelease=2.104,model=test
MAC,SSID,AuthMode,FirstSeen,Channel,Frequency,RSSI,CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,RCOIs,MfgrId,Type
aa:aa:aa:aa:aa:01,Alpha,Open,2026-04-08 11:32:44,1,2412,-55,48.880000,8.700000,400.0,5.0,,,WIFI
aa:aa:aa:aa:aa:01,Alpha,Open,2026-04-08 11:32:45,1,2412,-60,48.880010,8.700010,400.0,5.0,,,WIFI
bb:bb:bb:bb:bb:02,Beta,WPA2,2026-04-08 11:32:44,6,2437,-70,48.880000,8.700000,400.0,5.0,,,WIFI
cc:cc:cc:cc:cc:03,Gamma,WPA2,1970-01-01 00:00:00,11,2462,-80,48.880020,8.700020,400.0,20.0,,,WIFI
dd:dd:dd:dd:dd:04,Beacon,Open,2026-04-08 11:32:44,,7936,-90,48.880000,8.700000,400.0,5.0,,,BLE
ee:ee:ee:ee:ee:05,,WPA2,2026-04-08 11:32:46,36,5180,-65,48.880030,8.700030,400.0,5.0,,,WIFI
"""
    path = tmp_path / "sample_wigle.csv"
    path.write_text(csv_content, encoding="utf-8")
    return path


@pytest.fixture
def sample_raw_dataframe(sample_wigle_csv: Path) -> pd.DataFrame:
    return load_wifi_csv(sample_wigle_csv)


@pytest.fixture
def triangulation_wigle_csv(tmp_path: Path) -> Path:
    dataframe = _build_triangulation_dataframe()
    csv_lines = ["WigleWifi-1.6,appRelease=2.104,model=test", ",".join(dataframe.columns)]
    csv_lines.extend(
        ",".join(str(value) for value in row)
        for row in dataframe.itertuples(index=False, name=None)
    )

    path = tmp_path / "triangulation_wigle.csv"
    path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def triangulation_raw_dataframe(triangulation_wigle_csv: Path) -> pd.DataFrame:
    return load_wifi_csv(triangulation_wigle_csv)

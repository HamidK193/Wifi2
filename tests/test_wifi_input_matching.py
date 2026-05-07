import pandas as pd

from src.wifi_input_matching import match_wifi_measurements, normalize_bssid, normalize_ssid


def test_normalize_bssid_accepts_different_formats() -> None:
    assert normalize_bssid("AA-BB-CC-DD-EE-FF") == "aabbccddeeff"
    assert normalize_bssid("aa:bb:cc:dd:ee:ff") == "aabbccddeeff"


def test_normalize_ssid_accepts_small_spacing_and_case_changes() -> None:
    assert normalize_ssid("  My-Free WIFI  ") == "my free wifi"


def test_match_wifi_measurements_accepts_similar_ssid_and_bssid_format() -> None:
    access_points = pd.DataFrame(
        [
            {
                "network_id": "My Free Wifi | aa:bb:cc:dd:ee:ff",
                "ssid": "My Free Wifi",
                "bssid": "aa:bb:cc:dd:ee:ff",
                "scan_count": 5,
            }
        ]
    )

    matched, ignored = match_wifi_measurements("my-free wifi,AA-BB-CC-DD-EE-FF,-66", access_points)

    assert ignored.empty
    assert matched["network_id"].tolist() == ["My Free Wifi | aa:bb:cc:dd:ee:ff"]
    assert matched["rssi"].tolist() == [-66.0]


def test_match_wifi_measurements_reports_unknown_network() -> None:
    access_points = pd.DataFrame(
        [{"network_id": "Known | aa:bb:cc:dd:ee:ff", "ssid": "Known", "bssid": "aa:bb:cc:dd:ee:ff", "scan_count": 3}]
    )

    matched, ignored = match_wifi_measurements("Unknown,11:22:33:44:55:66,-70", access_points)

    assert matched.empty
    assert not ignored.empty

from src.fingerprint_localization import (
    estimate_position_from_fingerprint,
    get_scan_input_observations,
    parse_manual_wifi_input,
)
from src.preprocess_wifi_data import clean_wifi_data


def test_get_scan_input_observations_returns_network_fingerprint(sample_raw_dataframe) -> None:
    cleaned = clean_wifi_data(sample_raw_dataframe)

    observations = get_scan_input_observations(cleaned, "scan_01")

    assert len(observations) == 2
    assert set(observations["network_id"]) == {
        "Alpha | aa:aa:aa:aa:aa:01",
        "Beta | bb:bb:bb:bb:bb:02",
    }


def test_parse_manual_wifi_input_builds_network_ids() -> None:
    observations = parse_manual_wifi_input(
        "SSID,BSSID,RSSI\n"
        "Alpha,aa:aa:aa:aa:aa:01,-61\n"
        "Beta;bb:bb:bb:bb:bb:02;-72"
    )

    assert observations["network_id"].tolist() == [
        "Alpha | aa:aa:aa:aa:aa:01",
        "Beta | bb:bb:bb:bb:bb:02",
    ]


def test_estimate_position_from_fingerprint_returns_position(sample_raw_dataframe) -> None:
    cleaned = clean_wifi_data(sample_raw_dataframe)
    input_observations = get_scan_input_observations(cleaned, "scan_02")

    estimate = estimate_position_from_fingerprint(
        cleaned,
        input_observations,
        exclude_scan_id="scan_02",
        k=1,
    )

    assert estimate is not None
    assert estimate["matched_networks"] >= 1
    assert estimate["actual_latitude"] is not None
    assert estimate["error_m"] is not None

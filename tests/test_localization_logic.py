from src.localization_logic import (
    build_network_id,
    create_network_observations,
    create_network_summary,
    estimate_radius_from_rssi,
)
from src.preprocess_wifi_data import clean_wifi_data


def test_build_network_id_combines_ssid_and_bssid() -> None:
    assert build_network_id("Alpha", "aa:bb:cc:dd:ee:ff") == "Alpha | aa:bb:cc:dd:ee:ff"


def test_estimate_radius_from_rssi_shrinks_for_stronger_signal() -> None:
    strong_signal_radius = estimate_radius_from_rssi(-50)
    weak_signal_radius = estimate_radius_from_rssi(-80)

    assert strong_signal_radius < weak_signal_radius


def test_network_observations_and_summary_group_by_network_and_scan(sample_raw_dataframe) -> None:
    cleaned = clean_wifi_data(sample_raw_dataframe)
    observations = create_network_observations(cleaned)
    network_summary = create_network_summary(observations)

    assert len(observations) == 3
    assert observations["network_id"].nunique() == 2

    alpha_summary = network_summary.loc[
        network_summary["network_id"] == "Alpha | aa:aa:aa:aa:aa:01"
    ].iloc[0]
    assert int(alpha_summary["scan_count"]) == 2
    assert int(alpha_summary["total_observations"]) == 2

from src.fingerprint_localization import (
    estimate_position_from_fingerprint,
    estimate_route_positions,
    get_scan_input_observations,
    parse_manual_wifi_input,
    run_leave_one_scan_out_benchmark,
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


def test_leave_one_scan_out_benchmark_returns_position(triangulation_raw_dataframe) -> None:
    cleaned = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )

    estimate = run_leave_one_scan_out_benchmark(
        cleaned,
        "scan_01",
        min_matches=3,
    )

    assert estimate is not None
    assert estimate["matched_networks"] >= 3
    assert estimate["actual_latitude"] is not None
    assert estimate["error_m"] is not None


def test_compatibility_wrapper_uses_triangulated_access_points(triangulation_raw_dataframe) -> None:
    cleaned = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    input_observations = get_scan_input_observations(cleaned, "scan_02")

    estimate = estimate_position_from_fingerprint(
        cleaned,
        input_observations,
        exclude_scan_id="scan_02",
        min_matches=3,
    )

    assert estimate is not None
    assert estimate["matched_networks"] >= 3
    assert estimate["error_m"] is not None


def test_estimate_route_positions_returns_comparison_rows(sample_raw_dataframe) -> None:
    cleaned = clean_wifi_data(sample_raw_dataframe)
    scan_summary = (
        cleaned.groupby(["scan_id", "timestamp"], as_index=False)
        .agg(latitude=("latitude", "first"), longitude=("longitude", "first"))
    )

    route_comparison = estimate_route_positions(cleaned, scan_summary, k=1)

    assert "scan_id" in route_comparison.columns
    assert "estimated_latitude" in route_comparison.columns

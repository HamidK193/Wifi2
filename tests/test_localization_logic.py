from src.localization_logic import (
    build_network_id,
    create_network_observations,
    create_network_summary,
    estimate_overlap_points,
    estimate_position_from_access_points,
    estimate_radius_from_rssi,
    estimate_router_position_from_observations,
    triangulate_access_points,
    triangulate_scan_positions,
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


def test_triangulate_access_points_returns_quality_metrics(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )

    access_points = triangulate_access_points(calibration_dataframe)

    assert len(access_points) == 3
    assert set(access_points["quality_flag"]).issubset({"good", "usable", "weak"})
    assert (access_points["scan_count"] >= 3).all()


def test_router_position_requires_at_least_three_scan_points(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    observations = create_network_observations(calibration_dataframe)
    alpha_observations = observations.loc[
        observations["network_id"] == "Alpha | aa:aa:aa:aa:aa:01"
    ].copy()

    estimate = estimate_router_position_from_observations(alpha_observations)
    fallback_estimate = estimate_router_position_from_observations(alpha_observations.head(2))

    assert estimate is not None
    assert estimate["scan_count"] >= 3
    assert estimate["ssid"] == "Alpha"
    assert fallback_estimate is not None
    assert fallback_estimate["quality_flag"] == "fallback"


def test_overlap_points_can_require_three_supporting_circles(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    observations = create_network_observations(calibration_dataframe)
    alpha_observations = observations.loc[
        observations["network_id"] == "Alpha | aa:aa:aa:aa:aa:01"
    ].copy()

    overlap_points = estimate_overlap_points(alpha_observations, step_m=8, min_support=3)

    assert not overlap_points.empty
    assert (overlap_points["support_count"] >= 3).all()


def test_runtime_multilateration_works_without_runtime_gps(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    runtime_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=False,
        include_coordinates=False,
    )

    access_points = triangulate_access_points(calibration_dataframe)
    scan_positions = triangulate_scan_positions(runtime_dataframe, access_points)
    observations = create_network_observations(runtime_dataframe, scan_positions)
    input_observations = runtime_dataframe.loc[
        runtime_dataframe["scan_id"] == "scan_01",
        ["network_id", "ssid", "bssid", "rssi"],
    ].copy()

    estimate = estimate_position_from_access_points(access_points, input_observations)

    assert estimate is not None
    assert estimate["matched_networks"] >= 3
    assert estimate["confidence_score"] > 0
    assert len(observations.dropna(subset=["latitude", "longitude"])) > 0


def test_runtime_multilateration_accuracy_on_synthetic_data(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    runtime_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=False,
        include_coordinates=False,
    )

    access_points = triangulate_access_points(calibration_dataframe)
    scan_positions = triangulate_scan_positions(runtime_dataframe, access_points)

    assert len(scan_positions) >= 3
    assert scan_positions["residual_rmse"].median() < 35

from src.localization_logic import triangulate_access_points
from src.preprocess_wifi_data import clean_wifi_data
from src.localization_logic import triangulate_scan_positions
from src.route_estimation import (
    build_gps_route_matched,
    build_route_comparison_with_matched_gps,
    build_wifi_route_estimates,
    build_wifi_route_from_scan_positions,
    build_wknn_route_comparison,
    clean_route_comparison,
    estimate_scan_position_wknn,
    add_router_quality_metrics,
    smooth_route_positions,
    summarize_route_quality,
    summarize_wifi_route,
)


def test_wifi_route_estimates_return_snapped_route_points(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    access_points = triangulate_access_points(calibration_dataframe)
    osm_map = {
        "bounds": {"minlat": 48.879, "minlon": 8.699, "maxlat": 48.881, "maxlon": 8.701},
        "highways": [[(48.8798, 8.6996), (48.8805, 8.7010)]],
        "walkable_highways": [
            {"highway": "footway", "coordinates": [(48.8798, 8.6996), (48.8805, 8.7010)]}
        ],
        "buildings": [],
    }

    route_estimates = build_wifi_route_estimates(
        calibration_dataframe,
        access_points,
        osm_map,
        min_matches=2,
    )
    summary = summarize_wifi_route(route_estimates)

    assert not route_estimates.empty
    assert summary["estimated_scans"] == len(route_estimates)
    assert route_estimates["matched_access_points"].min() >= 2
    assert route_estimates["snap_distance_m"].notna().all()
    assert route_estimates["error_m"].notna().all()


def test_wifi_route_from_precomputed_scan_positions_is_fast_path(triangulation_raw_dataframe) -> None:
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
    osm_map = {
        "bounds": {"minlat": 48.879, "minlon": 8.699, "maxlat": 48.881, "maxlon": 8.701},
        "highways": [[(48.8798, 8.6996), (48.8805, 8.7010)]],
        "walkable_highways": [
            {"highway": "footway", "coordinates": [(48.8798, 8.6996), (48.8805, 8.7010)]}
        ],
        "buildings": [],
    }

    route_estimates = build_wifi_route_from_scan_positions(
        calibration_dataframe,
        scan_positions,
        osm_map,
        min_matches=2,
    )

    assert not route_estimates.empty
    assert set(route_estimates["method"]) == {"precomputed_wifi_multilateration"}
    assert route_estimates["matched_access_points"].min() >= 2


def test_clean_route_comparison_removes_low_quality_outliers() -> None:
    route_comparison = build_route_frame(
        [
            ("scan_01", 48.8800, 8.7000, 48.8800, 8.7000, 5, 10, 2),
            ("scan_02", 48.8801, 8.7001, 48.8801, 8.7001, 3, 10, 3),
            ("scan_03", 48.8802, 8.7002, 48.8802, 8.7002, 5, 150, 4),
            ("scan_04", 48.8803, 8.7003, 48.8816, 8.7016, 5, 20, 180),
            ("scan_05", 48.8804, 8.7004, 48.8804, 8.7004, 5, 20, 5),
        ]
    )

    cleaned = clean_route_comparison(route_comparison, min_aps=4, max_rmse_m=120, max_error_m=100, max_jump_m=80)

    assert cleaned["scan_id"].tolist() == ["scan_01", "scan_05"]
    assert "is_outlier" in cleaned.columns
    assert cleaned["is_outlier"].eq(False).all()


def test_clean_route_comparison_can_remove_weak_router_support() -> None:
    route_comparison = build_route_frame(
        [
            ("scan_01", 48.8800, 8.7000, 48.8800, 8.7000, 5, 10, 5),
            ("scan_02", 48.8801, 8.7001, 48.8801, 8.7001, 5, 10, 5),
        ]
    )
    route_comparison["median_router_rmse_m"] = [12.0, 25.0]

    cleaned = clean_route_comparison(
        route_comparison,
        min_aps=4,
        max_rmse_m=120,
        max_error_m=100,
        max_jump_m=80,
        max_median_router_rmse_m=15,
    )

    assert cleaned["scan_id"].tolist() == ["scan_01"]


def test_add_router_quality_metrics_summarizes_seen_access_points() -> None:
    route_comparison = build_route_frame(
        [("scan_01", 48.8800, 8.7000, 48.8800, 8.7000, 5, 10, 5)]
    )
    network_observations = __import__("pandas").DataFrame(
        [
            {"scan_id": "scan_01", "network_id": "a"},
            {"scan_id": "scan_01", "network_id": "b"},
            {"scan_id": "scan_01", "network_id": "c"},
        ]
    )
    access_points = __import__("pandas").DataFrame(
        [
            {"network_id": "a", "rmse_m": 10.0, "quality_flag": "good"},
            {"network_id": "b", "rmse_m": 14.0, "quality_flag": "usable"},
            {"network_id": "c", "rmse_m": 30.0, "quality_flag": "weak"},
        ]
    )

    enriched = add_router_quality_metrics(route_comparison, network_observations, access_points)

    assert int(enriched.loc[0, "seen_calibrated_aps"]) == 3
    assert float(enriched.loc[0, "median_router_rmse_m"]) == 14.0
    assert int(enriched.loc[0, "good_router_count"]) == 1
    assert int(enriched.loc[0, "usable_router_count"]) == 1
    assert int(enriched.loc[0, "weak_router_count"]) == 1


def test_wknn_scan_position_uses_similar_reference_scan(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    input_observations = calibration_dataframe.loc[
        calibration_dataframe["scan_id"] == "scan_01",
        ["network_id", "ssid", "bssid", "rssi"],
    ]
    reference_dataframe = calibration_dataframe.loc[calibration_dataframe["scan_id"] != "scan_01"].copy()

    estimate = estimate_scan_position_wknn(
        reference_dataframe,
        input_observations,
        k=2,
        min_matches=2,
    )

    assert estimate is not None
    assert estimate["matched_access_points"] >= 2
    assert estimate["method"] == "wknn_fingerprinting"


def test_wknn_ignores_networks_seen_in_fewer_than_three_scans(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    rare_network = calibration_dataframe.iloc[[0]].copy()
    rare_network["network_id"] = "Rare | 00:00:00:00:00:01"
    rare_network["ssid"] = "Rare"
    rare_network["bssid"] = "00:00:00:00:00:01"
    rare_network["rssi"] = -30

    reference_dataframe = __import__("pandas").concat(
        [
            calibration_dataframe.loc[calibration_dataframe["scan_id"] != "scan_01"],
            rare_network,
        ],
        ignore_index=True,
    )
    input_observations = __import__("pandas").concat(
        [
            calibration_dataframe.loc[
                calibration_dataframe["scan_id"] == "scan_01",
                ["network_id", "ssid", "bssid", "rssi"],
            ],
            rare_network.loc[:, ["network_id", "ssid", "bssid", "rssi"]],
        ],
        ignore_index=True,
    )

    estimate = estimate_scan_position_wknn(
        reference_dataframe,
        input_observations,
        k=2,
        min_matches=2,
    )

    assert estimate is not None
    assert estimate["matched_access_points"] == 3


def test_wknn_route_comparison_returns_smoothed_road_snapped_points(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    osm_map = {
        "bounds": {"minlat": 48.879, "minlon": 8.699, "maxlat": 48.881, "maxlon": 8.701},
        "highways": [[(48.8798, 8.6996), (48.8805, 8.7010)]],
        "walkable_highways": [
            {"highway": "footway", "coordinates": [(48.8798, 8.6996), (48.8805, 8.7010)]}
        ],
        "buildings": [],
    }

    route_estimates = build_wknn_route_comparison(
        calibration_dataframe,
        osm_map,
        k=2,
        min_matches=2,
    )

    assert not route_estimates.empty
    assert route_estimates["matched_access_points"].min() >= 2
    assert route_estimates["method"].str.contains("wknn_fingerprinting").all()
    assert route_estimates["method"].str.contains("road_snapped").all()


def test_gps_route_matching_and_wknn_matched_comparison_use_matched_gps(triangulation_raw_dataframe) -> None:
    calibration_dataframe = clean_wifi_data(
        triangulation_raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    osm_map = {
        "bounds": {"minlat": 48.879, "minlon": 8.699, "maxlat": 48.881, "maxlon": 8.701},
        "highways": [[(48.8798, 8.6996), (48.8805, 8.7010)]],
        "walkable_highways": [
            {"highway": "footway", "coordinates": [(48.8798, 8.6996), (48.8805, 8.7010)]}
        ],
        "buildings": [],
    }
    gps_route_matched = build_gps_route_matched(calibration_dataframe, osm_map, max_candidate_distance_m=80)
    route_estimates = build_wknn_route_comparison(
        calibration_dataframe,
        osm_map,
        k=2,
        min_matches=2,
        max_snap_distance_m=80,
    )

    matched_comparison = build_route_comparison_with_matched_gps(
        route_estimates,
        gps_route_matched,
        osm_map,
        max_candidate_distance_m=80,
    )

    assert not gps_route_matched.empty
    assert gps_route_matched["snapped"].all()
    assert not matched_comparison.empty
    assert "raw_actual_latitude" in matched_comparison.columns
    assert "gps_snap_distance_m" in matched_comparison.columns
    assert matched_comparison["method"].str.contains("route_matched").all()


def test_smooth_route_positions_reduces_large_jump() -> None:
    route_comparison = build_route_frame(
        [
            ("scan_01", 48.8800, 8.7000, 48.8800, 8.7000, 5, 10, 0),
            ("scan_02", 48.8801, 8.7001, 48.8830, 8.7030, 5, 10, 400),
            ("scan_03", 48.8802, 8.7002, 48.8802, 8.7002, 5, 10, 0),
        ]
    )

    smoothed = smooth_route_positions(route_comparison, alpha=0.25)

    raw_delta = abs(route_comparison.loc[1, "estimated_latitude"] - route_comparison.loc[0, "estimated_latitude"])
    smoothed_delta = abs(smoothed.loc[1, "estimated_latitude"] - smoothed.loc[0, "estimated_latitude"])
    assert smoothed_delta < raw_delta
    assert smoothed["method"].str.endswith("_smoothed").all()


def test_summarize_route_quality_adds_p90_and_label() -> None:
    route_comparison = build_route_frame(
        [
            ("scan_01", 48.8800, 8.7000, 48.8800, 8.7000, 5, 10, 5),
            ("scan_02", 48.8801, 8.7001, 48.8801, 8.7001, 5, 10, 15),
            ("scan_03", 48.8802, 8.7002, 48.8802, 8.7002, 5, 10, 25),
        ]
    )

    quality = summarize_route_quality(route_comparison)

    assert quality["used_scans"] == 3
    assert quality["p90_error_m"] is not None
    assert quality["quality_label"] in {"gut", "mittel", "schwach"}


def build_route_frame(rows: list[tuple[str, float, float, float, float, int, float, float]]):
    return __import__("pandas").DataFrame(
        [
            {
                "scan_id": scan_id,
                "timestamp": f"2026-04-08 12:00:{index:02d}",
                "actual_latitude": actual_latitude,
                "actual_longitude": actual_longitude,
                "raw_estimated_latitude": estimated_latitude,
                "raw_estimated_longitude": estimated_longitude,
                "estimated_latitude": estimated_latitude,
                "estimated_longitude": estimated_longitude,
                "matched_access_points": matched_access_points,
                "residual_rmse": residual_rmse,
                "snap_distance_m": 1.0,
                "error_m": error_m,
                "method": "test",
            }
            for index, (
                scan_id,
                actual_latitude,
                actual_longitude,
                estimated_latitude,
                estimated_longitude,
                matched_access_points,
                residual_rmse,
                error_m,
            ) in enumerate(rows, start=1)
        ]
    )

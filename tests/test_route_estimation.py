from src.localization_logic import triangulate_access_points
from src.preprocess_wifi_data import clean_wifi_data
from src.localization_logic import triangulate_scan_positions
from src.route_estimation import (
    build_wifi_route_estimates,
    build_wifi_route_from_scan_positions,
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

import pandas as pd

from src.road_constraints import (
    find_walkable_road_candidates,
    match_route_to_walkable_roads,
    project_point_to_segment,
    snap_position_to_nearest_road,
)


def test_project_point_to_segment_projects_between_segment_endpoints() -> None:
    projected_latitude, projected_longitude = project_point_to_segment(
        48.8801,
        8.7002,
        (48.8800, 8.7000),
        (48.8800, 8.7004),
    )

    assert round(projected_latitude, 4) == 48.8800
    assert 8.7000 <= projected_longitude <= 8.7004


def test_snap_position_to_nearest_road_returns_walkable_way() -> None:
    osm_map = {
        "walkable_highways": [
            {"highway": "footway", "coordinates": [(48.8800, 8.7000), (48.8800, 8.7004)]},
            {"highway": "residential", "coordinates": [(48.8810, 8.7000), (48.8810, 8.7004)]},
        ]
    }

    snapped = snap_position_to_nearest_road(48.8801, 8.7002, osm_map)

    assert snapped["snapped"] is True
    assert snapped["road_type"] == "footway"
    assert snapped["snap_distance_m"] > 0


def test_snap_position_without_roads_keeps_raw_position() -> None:
    snapped = snap_position_to_nearest_road(48.8801, 8.7002, {"walkable_highways": []})

    assert snapped["snapped"] is False
    assert snapped["latitude"] == 48.8801
    assert snapped["longitude"] == 8.7002


def test_snap_position_too_far_from_road_keeps_raw_position() -> None:
    osm_map = {
        "walkable_highways": [
            {"highway": "footway", "coordinates": [(48.8900, 8.7100), (48.8900, 8.7110)]}
        ]
    }

    snapped = snap_position_to_nearest_road(48.8801, 8.7002, osm_map, max_snap_distance_m=60)

    assert snapped["snapped"] is False
    assert snapped["latitude"] == 48.8801
    assert snapped["longitude"] == 8.7002


def test_walkable_candidates_prefer_footway_over_road_when_similar_distance() -> None:
    osm_map = {
        "walkable_highways": [
            {"highway": "primary", "coordinates": [(48.88000, 8.7000), (48.88000, 8.7005)]},
            {"highway": "footway", "coordinates": [(48.88004, 8.7000), (48.88004, 8.7005)]},
        ]
    }

    candidates = find_walkable_road_candidates(48.88003, 8.7002, osm_map, max_candidate_distance_m=20)

    assert candidates
    assert candidates[0]["road_type"] == "footway"


def test_route_matching_keeps_route_on_plausible_same_way() -> None:
    osm_map = {
        "walkable_highways": [
            {"highway": "footway", "coordinates": [(48.8800, 8.7000), (48.8800, 8.7010)]},
            {"highway": "residential", "coordinates": [(48.8802, 8.7000), (48.8802, 8.7010)]},
        ]
    }
    route_points = pd.DataFrame(
        [
            {"scan_id": "scan_01", "timestamp": "2026-04-08 12:00:01", "latitude": 48.88001, "longitude": 8.7001},
            {"scan_id": "scan_02", "timestamp": "2026-04-08 12:00:02", "latitude": 48.88003, "longitude": 8.7002},
            {"scan_id": "scan_03", "timestamp": "2026-04-08 12:00:03", "latitude": 48.88001, "longitude": 8.7003},
        ]
    )

    matched = match_route_to_walkable_roads(route_points, osm_map, max_candidate_distance_m=30)

    assert matched["snapped"].all()
    assert matched["road_type"].eq("footway").all()
    assert matched["segment_id"].nunique() == 1

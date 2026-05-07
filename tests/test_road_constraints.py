from src.road_constraints import project_point_to_segment, snap_position_to_nearest_road


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

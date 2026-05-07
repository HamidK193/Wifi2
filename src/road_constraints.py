import math

from src.localization_logic import LAT_METERS, calculate_distance_m

WALKABLE_HIGHWAY_TYPES = {
    "footway",
    "pedestrian",
    "path",
    "steps",
    "cycleway",
    "living_street",
    "residential",
    "service",
    "primary",
    "secondary",
    "tertiary",
    "primary_link",
    "secondary_link",
    "tertiary_link",
}


def snap_position_to_nearest_road(
    latitude: float,
    longitude: float,
    osm_map: dict[str, object],
) -> dict[str, object]:
    walkable_highways = osm_map.get("walkable_highways", [])
    if not walkable_highways:
        return _unsnapped_position(latitude, longitude)

    best_point: dict[str, object] | None = None
    best_distance = math.inf

    for highway in walkable_highways:
        coordinates = highway.get("coordinates", [])
        road_type = highway.get("highway", "unknown")
        for start, end in zip(coordinates, coordinates[1:]):
            projected_latitude, projected_longitude = project_point_to_segment(latitude, longitude, start, end)
            distance = calculate_distance_m(
                latitude,
                longitude,
                projected_latitude,
                projected_longitude,
                latitude,
            )
            if distance < best_distance:
                best_distance = distance
                best_point = {
                    "latitude": projected_latitude,
                    "longitude": projected_longitude,
                    "snap_distance_m": float(distance),
                    "road_type": road_type,
                    "snapped": True,
                }

    if best_point is None:
        return _unsnapped_position(latitude, longitude)

    return best_point


def project_point_to_segment(
    latitude: float,
    longitude: float,
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[float, float]:
    mean_latitude = (latitude + start[0] + end[0]) / 3
    lon_scale = LAT_METERS * max(0.1, math.cos(math.radians(mean_latitude)))

    point_x = longitude * lon_scale
    point_y = latitude * LAT_METERS
    start_x = start[1] * lon_scale
    start_y = start[0] * LAT_METERS
    end_x = end[1] * lon_scale
    end_y = end[0] * LAT_METERS

    segment_x = end_x - start_x
    segment_y = end_y - start_y
    segment_length_squared = segment_x**2 + segment_y**2
    if segment_length_squared == 0:
        return start

    t = ((point_x - start_x) * segment_x + (point_y - start_y) * segment_y) / segment_length_squared
    t = max(0.0, min(1.0, t))

    projected_x = start_x + t * segment_x
    projected_y = start_y + t * segment_y
    return projected_y / LAT_METERS, projected_x / lon_scale


def _unsnapped_position(latitude: float, longitude: float) -> dict[str, object]:
    return {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "snap_distance_m": None,
        "road_type": None,
        "snapped": False,
    }

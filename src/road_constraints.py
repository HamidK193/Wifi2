import math

import pandas as pd

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
ROAD_TYPE_PENALTY = {
    "footway": 0.0,
    "pedestrian": 0.0,
    "path": 2.0,
    "steps": 3.0,
    "cycleway": 4.0,
    "living_street": 6.0,
    "residential": 8.0,
    "service": 10.0,
    "tertiary": 16.0,
    "secondary": 22.0,
    "primary": 28.0,
    "tertiary_link": 18.0,
    "secondary_link": 24.0,
    "primary_link": 30.0,
}


def snap_position_to_nearest_road(
    latitude: float,
    longitude: float,
    osm_map: dict[str, object],
    *,
    max_snap_distance_m: float = 60.0,
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

    if best_point is None or best_distance > max_snap_distance_m:
        return _unsnapped_position(latitude, longitude)

    return best_point


def find_walkable_road_candidates(
    latitude: float,
    longitude: float,
    osm_map: dict[str, object],
    *,
    max_candidate_distance_m: float = 30.0,
    max_candidates: int = 6,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for highway_index, highway in enumerate(osm_map.get("walkable_highways", [])):
        coordinates = highway.get("coordinates", [])
        road_type = highway.get("highway", "unknown")
        for segment_index, (start, end) in enumerate(zip(coordinates, coordinates[1:])):
            projected_latitude, projected_longitude = project_point_to_segment(latitude, longitude, start, end)
            distance = calculate_distance_m(
                latitude,
                longitude,
                projected_latitude,
                projected_longitude,
                latitude,
            )
            if distance > max_candidate_distance_m:
                continue
            type_penalty = ROAD_TYPE_PENALTY.get(str(road_type), 20.0)
            candidates.append(
                {
                    "latitude": projected_latitude,
                    "longitude": projected_longitude,
                    "snap_distance_m": float(distance),
                    "road_type": road_type,
                    "snapped": True,
                    "segment_id": f"{highway_index}:{segment_index}",
                    "candidate_score": float(distance + type_penalty),
                }
            )

    return sorted(candidates, key=lambda candidate: candidate["candidate_score"])[:max_candidates]


def match_route_to_walkable_roads(
    route_points: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    latitude_column: str = "latitude",
    longitude_column: str = "longitude",
    max_candidate_distance_m: float = 30.0,
    transition_weight: float = 0.35,
    road_change_penalty: float = 8.0,
) -> pd.DataFrame:
    if route_points.empty:
        return pd.DataFrame(columns=_matched_route_columns(route_points))

    ordered = route_points.reset_index(drop=True).copy()
    candidate_layers = [
        _candidates_for_route_row(
            row,
            osm_map,
            latitude_column=latitude_column,
            longitude_column=longitude_column,
            max_candidate_distance_m=max_candidate_distance_m,
        )
        for _, row in ordered.iterrows()
    ]

    costs: list[list[float]] = []
    previous_indexes: list[list[int | None]] = []
    for index, candidates in enumerate(candidate_layers):
        layer_costs: list[float] = []
        layer_previous_indexes: list[int | None] = []
        if index == 0:
            for candidate in candidates:
                layer_costs.append(float(candidate["candidate_score"]))
                layer_previous_indexes.append(None)
        else:
            previous_candidates = candidate_layers[index - 1]
            previous_costs = costs[index - 1]
            raw_jump_m = calculate_distance_m(
                float(ordered.loc[index - 1, latitude_column]),
                float(ordered.loc[index - 1, longitude_column]),
                float(ordered.loc[index, latitude_column]),
                float(ordered.loc[index, longitude_column]),
                float(ordered.loc[index, latitude_column]),
            )
            for candidate in candidates:
                best_cost = math.inf
                best_previous_index: int | None = None
                for previous_index, previous_candidate in enumerate(previous_candidates):
                    candidate_jump_m = calculate_distance_m(
                        float(previous_candidate["latitude"]),
                        float(previous_candidate["longitude"]),
                        float(candidate["latitude"]),
                        float(candidate["longitude"]),
                        float(candidate["latitude"]),
                    )
                    transition_cost = abs(candidate_jump_m - raw_jump_m) * transition_weight
                    if candidate["segment_id"] != previous_candidate["segment_id"] and raw_jump_m < 25:
                        transition_cost += road_change_penalty
                    total_cost = previous_costs[previous_index] + float(candidate["candidate_score"]) + transition_cost
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_previous_index = previous_index
                layer_costs.append(best_cost)
                layer_previous_indexes.append(best_previous_index)
        costs.append(layer_costs)
        previous_indexes.append(layer_previous_indexes)

    best_index = min(range(len(costs[-1])), key=lambda candidate_index: costs[-1][candidate_index])
    selected_indexes = [best_index]
    for layer_index in range(len(candidate_layers) - 1, 0, -1):
        previous_index = previous_indexes[layer_index][selected_indexes[-1]]
        selected_indexes.append(0 if previous_index is None else previous_index)
    selected_indexes.reverse()

    matched_rows: list[dict[str, object]] = []
    for row_index, candidate_index in enumerate(selected_indexes):
        source_row = ordered.iloc[row_index].to_dict()
        candidate = candidate_layers[row_index][candidate_index]
        matched_rows.append(
            {
                **source_row,
                "raw_latitude": float(source_row[latitude_column]),
                "raw_longitude": float(source_row[longitude_column]),
                "latitude": float(candidate["latitude"]),
                "longitude": float(candidate["longitude"]),
                "snap_distance_m": candidate["snap_distance_m"],
                "road_type": candidate["road_type"],
                "snapped": candidate["snapped"],
                "segment_id": candidate["segment_id"],
                "match_score": candidate["candidate_score"],
                "candidate_count": len(candidate_layers[row_index]),
            }
        )

    return pd.DataFrame(matched_rows)


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


def _candidates_for_route_row(
    row: pd.Series,
    osm_map: dict[str, object],
    *,
    latitude_column: str,
    longitude_column: str,
    max_candidate_distance_m: float,
) -> list[dict[str, object]]:
    latitude = float(row[latitude_column])
    longitude = float(row[longitude_column])
    candidates = find_walkable_road_candidates(
        latitude,
        longitude,
        osm_map,
        max_candidate_distance_m=max_candidate_distance_m,
    )
    if candidates:
        return candidates

    unsnapped = _unsnapped_position(latitude, longitude)
    unsnapped.update(
        {
            "segment_id": "unsnapped",
            "candidate_score": max_candidate_distance_m + 100.0,
            "candidate_count": 1,
        }
    )
    return [unsnapped]


def _matched_route_columns(route_points: pd.DataFrame) -> list[str]:
    return list(route_points.columns) + [
        "raw_latitude",
        "raw_longitude",
        "latitude",
        "longitude",
        "snap_distance_m",
        "road_type",
        "snapped",
        "segment_id",
        "match_score",
        "candidate_count",
    ]

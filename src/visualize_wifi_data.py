from pathlib import Path
from xml.etree import ElementTree as ET

import folium
import pandas as pd
from folium.plugins import PolyLineTextPath

from src.road_constraints import WALKABLE_HIGHWAY_TYPES

MAX_ROUTE_DETAIL_POINTS = 120


def load_osm_map(osm_path: str | Path) -> dict[str, object]:
    path = Path(osm_path)
    tree = ET.parse(path)
    root = tree.getroot()

    bounds_element = root.find("bounds")
    if bounds_element is None:
        raise ValueError("Die OSM-Datei enthaelt keine bounds-Angabe.")

    bounds = {
        "minlat": float(bounds_element.attrib["minlat"]),
        "minlon": float(bounds_element.attrib["minlon"]),
        "maxlat": float(bounds_element.attrib["maxlat"]),
        "maxlon": float(bounds_element.attrib["maxlon"]),
    }

    node_coordinates: dict[str, tuple[float, float]] = {}
    highways: list[list[tuple[float, float]]] = []
    walkable_highways: list[dict[str, object]] = []
    buildings: list[list[tuple[float, float]]] = []

    for element in root.findall("node"):
        node_id = element.attrib.get("id")
        lat = element.attrib.get("lat")
        lon = element.attrib.get("lon")
        if node_id and lat and lon:
            node_coordinates[node_id] = (float(lat), float(lon))

    for way in root.findall("way"):
        node_refs = [node_ref.attrib["ref"] for node_ref in way.findall("nd")]
        coordinates = [node_coordinates[node_ref] for node_ref in node_refs if node_ref in node_coordinates]
        if len(coordinates) < 2:
            continue

        tags = {
            tag.attrib.get("k", ""): tag.attrib.get("v", "")
            for tag in way.findall("tag")
        }

        highway_type = tags.get("highway")
        if highway_type:
            highways.append(coordinates)
            if highway_type in WALKABLE_HIGHWAY_TYPES:
                walkable_highways.append({"highway": highway_type, "coordinates": coordinates})

        if "building" in tags and len(coordinates) >= 3:
            polygon = coordinates
            if polygon[0] != polygon[-1]:
                polygon = polygon + [polygon[0]]
            buildings.append(polygon)

    return {
        "bounds": bounds,
        "highways": highways,
        "walkable_highways": walkable_highways,
        "buildings": buildings,
    }


def build_simple_location_map(
    osm_map: dict[str, object],
    position_estimate: dict[str, object] | None,
) -> folium.Map:
    center_lat, center_lon = _get_simple_map_center(position_estimate, osm_map["bounds"])
    location_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=18,
        tiles=None,
        control_scale=True,
    )

    add_osm_base_layers(location_map, osm_map)
    add_simple_position_marker(location_map, position_estimate)
    fit_simple_map_to_position(location_map, position_estimate, osm_map["bounds"])
    return location_map


def build_router_map(
    osm_map: dict[str, object],
    scan_summary: pd.DataFrame,
    selected_observations: pd.DataFrame,
    overlap_points: pd.DataFrame,
    network_colors: dict[str, str],
    access_points: pd.DataFrame,
    position_estimate: object | None = None,
    route_comparison: pd.DataFrame | None = None,
    show_scan_markers: bool = True,
    show_access_points: bool = True,
) -> folium.Map:
    center_lat, center_lon = _get_map_center(scan_summary, access_points, osm_map["bounds"])

    router_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=18,
        tiles=None,
        control_scale=True,
    )

    add_osm_base_layers(router_map, osm_map)
    add_route_comparison_markers(router_map, route_comparison)
    if show_scan_markers:
        add_scan_markers(router_map, scan_summary)
    if show_access_points:
        add_access_point_markers(router_map, access_points)
    add_router_radius_circles(router_map, selected_observations, network_colors)
    add_overlap_markers(router_map, overlap_points)
    add_position_estimate_marker(router_map, position_estimate)
    fit_map_to_bounds(router_map, scan_summary, access_points, osm_map["bounds"], route_comparison)
    folium.LayerControl(collapsed=False).add_to(router_map)

    return router_map


def build_router_estimation_map(
    osm_map: dict[str, object],
    selected_observations: pd.DataFrame,
    router_estimates: pd.DataFrame,
    ssid_colors: dict[str, str],
    overlap_points: pd.DataFrame,
) -> folium.Map:
    center_lat, center_lon = _get_router_estimation_center(selected_observations, router_estimates, osm_map["bounds"])
    router_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=18,
        tiles=None,
        control_scale=True,
    )

    add_osm_base_layers(router_map, osm_map)
    add_router_estimation_scan_markers(router_map, selected_observations)
    add_router_estimation_circles(router_map, selected_observations, ssid_colors)
    add_overlap_markers(router_map, overlap_points)
    add_estimated_router_markers(router_map, router_estimates)
    fit_router_estimation_map(router_map, selected_observations, router_estimates, osm_map["bounds"])
    return router_map


def build_route_estimation_map(
    osm_map: dict[str, object],
    route_estimates: pd.DataFrame,
) -> folium.Map:
    center_lat, center_lon = _get_route_estimation_center(route_estimates, osm_map["bounds"])
    route_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=17,
        tiles=None,
        control_scale=True,
    )

    add_osm_base_layers(route_map, osm_map)
    add_gps_and_wifi_routes(route_map, route_estimates)
    fit_route_estimation_map(route_map, route_estimates, osm_map["bounds"])
    return route_map


def add_osm_base_layers(router_map: folium.Map, osm_map: dict[str, object]) -> None:
    building_group = folium.FeatureGroup(name="Gebaeude", show=True)
    highway_group = folium.FeatureGroup(name="Strassen und Wege", show=True)

    for building in osm_map["buildings"]:
        folium.Polygon(
            locations=building,
            color="#9ca3af",
            weight=1,
            fill=True,
            fill_color="#e5e7eb",
            fill_opacity=0.5,
        ).add_to(building_group)

    for highway in osm_map["highways"]:
        folium.PolyLine(
            locations=highway,
            color="#6b7280",
            weight=2,
            opacity=0.8,
        ).add_to(highway_group)

    building_group.add_to(router_map)
    highway_group.add_to(router_map)


def add_scan_markers(router_map: folium.Map, scan_summary: pd.DataFrame) -> None:
    valid_scans = scan_summary.dropna(subset=["latitude", "longitude"]).copy()
    if valid_scans.empty:
        return

    scan_group = folium.FeatureGroup(name="Triangulierte Scan-Punkte", show=True)

    for _, row in valid_scans.iterrows():
        popup_text = (
            f"Scan: {row['scan_id']}<br>"
            f"Zeit: {row['timestamp']}<br>"
            f"Sichtbare Netzwerke: {int(row['visible_networks'])}<br>"
            f"Mittlere RSSI: {row['mean_rssi']:.1f} dBm"
        )
        if "matched_access_points" in row and pd.notna(row["matched_access_points"]):
            popup_text += f"<br>Gematchte APs: {int(row['matched_access_points'])}"
        if "residual_rmse" in row and pd.notna(row["residual_rmse"]):
            popup_text += f"<br>Residual-RMSE: {float(row['residual_rmse']):.1f} m"

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            color="#111827",
            fill=True,
            fill_color="#ffffff",
            fill_opacity=1.0,
            weight=2,
            popup=folium.Popup(popup_text, max_width=260),
            tooltip=row["scan_id"],
        ).add_to(scan_group)

    scan_group.add_to(router_map)


def add_access_point_markers(router_map: folium.Map, access_points: pd.DataFrame) -> None:
    valid_access_points = access_points.dropna(subset=["latitude", "longitude"]).copy()
    if valid_access_points.empty:
        return

    access_point_group = folium.FeatureGroup(name="Triangulierte Access Points", show=True)

    for _, row in valid_access_points.iterrows():
        popup_text = (
            f"SSID: {row['ssid']}<br>"
            f"BSSID: {row['bssid']}<br>"
            f"Kalibrierungs-Scans: {int(row['scan_count'])}<br>"
            f"RMSE: {row['rmse_m']:.1f} m<br>"
            f"Qualitaet: {row['quality_flag']}"
        )
        marker_color = "green" if row["quality_flag"] == "good" else "orange"

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.85,
            weight=2,
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=f"AP: {row['ssid']} | {row['bssid']}",
        ).add_to(access_point_group)

    access_point_group.add_to(router_map)


def add_router_radius_circles(
    router_map: folium.Map,
    selected_observations: pd.DataFrame,
    network_colors: dict[str, str],
) -> None:
    valid_observations = selected_observations.dropna(subset=["latitude", "longitude"]).copy()
    if valid_observations.empty:
        return

    radius_group = folium.FeatureGroup(name="Moegliche Nutzer-Radien", show=True)

    for _, row in valid_observations.iterrows():
        color = network_colors.get(row["network_id"], "#2563eb")
        popup_text = (
            f"SSID: {row['ssid']}<br>"
            f"BSSID: {row['bssid']}<br>"
            f"Netzwerk-ID: {row['network_id']}<br>"
            f"Scan: {row['scan_id']}<br>"
            f"RSSI: {row['mean_rssi']:.1f} dBm<br>"
            f"Radius-Schaetzung: {row['estimated_radius_m']:.1f} m<br>"
            f"Beobachtungen im Scan: {int(row['observation_count'])}"
        )

        folium.Circle(
            location=[row["latitude"], row["longitude"]],
            radius=float(row["estimated_radius_m"]),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.14,
            weight=2,
            popup=folium.Popup(popup_text, max_width=320),
            tooltip=f"{row['ssid']} | {row['bssid']}",
        ).add_to(radius_group)

    radius_group.add_to(router_map)


def add_router_estimation_scan_markers(router_map: folium.Map, selected_observations: pd.DataFrame) -> None:
    if selected_observations.empty or not {"latitude", "longitude"}.issubset(selected_observations.columns):
        return

    valid_observations = selected_observations.dropna(subset=["latitude", "longitude"]).copy()
    if valid_observations.empty:
        return

    scan_group = folium.FeatureGroup(name="Messpunkte", show=True)
    scan_positions = (
        valid_observations.groupby(["scan_id", "timestamp"], as_index=False)
        .agg(
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            networks=("network_id", "nunique"),
            strongest_rssi=("strongest_rssi", "max"),
        )
        .sort_values("timestamp")
    )

    for _, row in scan_positions.iterrows():
        popup_text = (
            f"Messpunkt: {row['scan_id']}<br>"
            f"Zeit: {row['timestamp']}<br>"
            f"Gefilterte Netzwerke: {int(row['networks'])}<br>"
            f"Staerkstes RSSI: {row['strongest_rssi']:.1f} dBm"
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            color="#111827",
            fill=True,
            fill_color="#ffffff",
            fill_opacity=1.0,
            weight=2,
            popup=folium.Popup(popup_text, max_width=260),
            tooltip=f"Messpunkt {row['scan_id']}",
        ).add_to(scan_group)

    scan_group.add_to(router_map)


def add_router_estimation_circles(
    router_map: folium.Map,
    selected_observations: pd.DataFrame,
    ssid_colors: dict[str, str],
) -> None:
    if selected_observations.empty or not {"latitude", "longitude"}.issubset(selected_observations.columns):
        return

    valid_observations = selected_observations.dropna(subset=["latitude", "longitude"]).copy()
    if valid_observations.empty:
        return

    radius_group = folium.FeatureGroup(name="RSSI-Radiuskreise", show=True)

    for _, row in valid_observations.iterrows():
        color = ssid_colors.get(row["ssid"], "#2563eb")
        popup_text = (
            f"SSID: {row['ssid']}<br>"
            f"BSSID: {row['bssid']}<br>"
            f"Scan: {row['scan_id']}<br>"
            f"RSSI: {row['mean_rssi']:.1f} dBm<br>"
            f"Radius: {row['estimated_radius_m']:.1f} m<br>"
            f"Beobachtungen: {int(row['observation_count'])}"
        )

        folium.Circle(
            location=[row["latitude"], row["longitude"]],
            radius=float(row["estimated_radius_m"]),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.12,
            weight=2,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['ssid']} | {row['bssid']}",
        ).add_to(radius_group)

    radius_group.add_to(router_map)


def add_estimated_router_markers(router_map: folium.Map, router_estimates: pd.DataFrame) -> None:
    if router_estimates.empty or not {"latitude", "longitude"}.issubset(router_estimates.columns):
        return

    valid_routers = router_estimates.dropna(subset=["latitude", "longitude"]).copy()
    if valid_routers.empty:
        return

    router_group = folium.FeatureGroup(name="Geschaetzte Routerstandorte", show=True)

    for _, row in valid_routers.iterrows():
        popup_text = (
            "Geschaetzter Routerstandort<br>"
            f"SSID: {row['ssid']}<br>"
            f"BSSID: {row['bssid']}<br>"
            f"Scans: {int(row['scan_count'])}<br>"
            f"RMSE: {row['rmse_m']:.1f} m<br>"
            f"Qualitaet: {row['quality_flag']}"
        )
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=f"Router: {row['ssid']} | {row['bssid']}",
            icon=folium.Icon(color="red", icon="signal", prefix="glyphicon"),
        ).add_to(router_group)

    router_group.add_to(router_map)


def add_overlap_markers(router_map: folium.Map, overlap_points: pd.DataFrame) -> None:
    if overlap_points.empty:
        return

    overlap_group = folium.FeatureGroup(name="Kreis-Ueberlappung", show=True)

    for _, row in overlap_points.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            color=row.get("color", "#dc2626"),
            fill=True,
            fill_color=row.get("color", "#ef4444"),
            fill_opacity=0.75,
            weight=1,
            popup=folium.Popup(
                "Ueberlappungspunkt<br>"
                f"SSID: {row.get('ssid', '-')}"
                f"<br>BSSID: {row.get('bssid', '-')}"
                f"<br>Unterstuetzung: {int(row['support_count'])} Kreise",
                max_width=220,
            ),
        ).add_to(overlap_group)

    overlap_group.add_to(router_map)


def add_position_estimate_marker(router_map: folium.Map, position_estimate: object | None) -> None:
    if position_estimate is None:
        return

    estimate_group = folium.FeatureGroup(name="Geschaetzter Standort", show=True)
    popup_text = (
        "Geschaetzter Standort<br>"
        f"Gematchte APs: {position_estimate['matched_networks']}<br>"
        f"Residual-RMSE: {position_estimate['residual_rmse']:.1f} m<br>"
        f"Konfidenz: {position_estimate['confidence_score']:.2f}"
    )
    if position_estimate["error_m"] is not None:
        popup_text += f"<br>Benchmark-Fehler: {position_estimate['error_m']:.1f} m"

    folium.Marker(
        location=[position_estimate["latitude"], position_estimate["longitude"]],
        popup=folium.Popup(popup_text, max_width=260),
        tooltip="Geschaetzter Standort",
        icon=folium.Icon(color="red", icon="screenshot", prefix="glyphicon"),
    ).add_to(estimate_group)

    if position_estimate["actual_latitude"] is not None and position_estimate["actual_longitude"] is not None:
        folium.Marker(
            location=[position_estimate["actual_latitude"], position_estimate["actual_longitude"]],
            popup=folium.Popup("Benchmark-Referenzpunkt", max_width=220),
            tooltip="Benchmark-Referenzpunkt",
            icon=folium.Icon(color="green", icon="map-marker", prefix="glyphicon"),
        ).add_to(estimate_group)

    estimate_group.add_to(router_map)


def add_simple_position_marker(location_map: folium.Map, position_estimate: dict[str, object] | None) -> None:
    if position_estimate is None:
        return

    raw_latitude = position_estimate["raw_latitude"]
    raw_longitude = position_estimate["raw_longitude"]
    latitude = position_estimate["latitude"]
    longitude = position_estimate["longitude"]

    snap_distance = position_estimate.get("snap_distance_m")
    snap_text = f"{snap_distance:.1f} m" if snap_distance is not None else "nicht verfuegbar"
    popup_text = (
        "Geschaetzter Standort auf Strasse/Fussweg<br>"
        f"Gematchte Netzwerke: {position_estimate['matched_networks']}<br>"
        f"RMSE: {position_estimate['residual_rmse']:.1f} m<br>"
        f"Snap-Distanz: {snap_text}"
    )

    folium.Marker(
        location=[latitude, longitude],
        popup=folium.Popup(popup_text, max_width=280),
        tooltip="Geschaetzter Standort",
        icon=folium.Icon(color="red", icon="map-marker", prefix="glyphicon"),
    ).add_to(location_map)

    if position_estimate.get("snapped"):
        folium.CircleMarker(
            location=[raw_latitude, raw_longitude],
            radius=4,
            color="#f97316",
            fill=True,
            fill_color="#f97316",
            fill_opacity=0.8,
            tooltip="Roh-Schaetzung vor Strassen-Snapping",
        ).add_to(location_map)
        folium.PolyLine(
            locations=[[raw_latitude, raw_longitude], [latitude, longitude]],
            color="#f97316",
            weight=2,
            opacity=0.8,
            dash_array="5, 7",
            tooltip="Korrektur auf naechste begehbare Strasse",
        ).add_to(location_map)


def add_route_comparison_markers(router_map: folium.Map, route_comparison: pd.DataFrame | None) -> None:
    if route_comparison is None or route_comparison.empty:
        return

    valid_rows = route_comparison.dropna(
        subset=[
            "actual_latitude",
            "actual_longitude",
            "estimated_latitude",
            "estimated_longitude",
        ]
    ).copy()
    if valid_rows.empty:
        return

    comparison_group = folium.FeatureGroup(name="GPS-vs-WLAN-Routenvergleich", show=True)
    actual_route = valid_rows[["actual_latitude", "actual_longitude"]].values.tolist()

    if len(actual_route) >= 2:
        folium.PolyLine(
            locations=actual_route,
            color="#dc2626",
            weight=4,
            opacity=0.85,
            tooltip="Aufgezeichnete GPS-Route",
        ).add_to(comparison_group)

    detail_rows = _sample_route_detail_rows(valid_rows)
    for _, row in detail_rows.iterrows():
        folium.CircleMarker(
            location=[row["actual_latitude"], row["actual_longitude"]],
            radius=3,
            color="#991b1b",
            fill=True,
            fill_color="#ffffff",
            fill_opacity=1.0,
            weight=2,
            popup=folium.Popup(f"GPS-Referenz<br>Scan: {row['scan_id']}", max_width=220),
            tooltip=f"GPS {row['scan_id']}",
        ).add_to(comparison_group)

        folium.CircleMarker(
            location=[row["estimated_latitude"], row["estimated_longitude"]],
            radius=5,
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.95,
            weight=2,
            popup=folium.Popup(
                f"WLAN-Schaetzung<br>Scan: {row['scan_id']}"
                f"<br>Fehler: {row['error_m']:.1f} m"
                f"<br>AP-Treffer: {int(row['matched_access_points'])}"
                f"<br>Residual-RMSE: {row['residual_rmse']:.1f} m",
                max_width=240,
            ),
            tooltip=f"WLAN-Schaetzung {row['scan_id']}",
        ).add_to(comparison_group)

        line = folium.PolyLine(
            locations=[
                [row["actual_latitude"], row["actual_longitude"]],
                [row["estimated_latitude"], row["estimated_longitude"]],
            ],
            color="#f97316",
            weight=2,
            opacity=0.65,
            dash_array="6, 8",
        )
        line.add_to(comparison_group)
        PolyLineTextPath(
            line,
            ">",
            repeat=True,
            offset=7,
            attributes={"fill": "#f97316", "font-weight": "bold", "font-size": "12"},
        ).add_to(comparison_group)

    comparison_group.add_to(router_map)


def add_gps_and_wifi_routes(route_map: folium.Map, route_estimates: pd.DataFrame) -> None:
    if route_estimates.empty:
        return

    valid_rows = route_estimates.dropna(
        subset=[
            "actual_latitude",
            "actual_longitude",
            "estimated_latitude",
            "estimated_longitude",
        ]
    ).copy()
    if valid_rows.empty:
        return

    route_group = folium.FeatureGroup(name="GPS- und WLAN-Laufweg", show=True)
    gps_route = valid_rows[["actual_latitude", "actual_longitude"]].values.tolist()
    wifi_route = valid_rows[["estimated_latitude", "estimated_longitude"]].values.tolist()
    if {"raw_actual_latitude", "raw_actual_longitude"}.issubset(valid_rows.columns):
        raw_gps_route = valid_rows[["raw_actual_latitude", "raw_actual_longitude"]].dropna().values.tolist()
        if len(raw_gps_route) >= 2:
            folium.PolyLine(
                locations=raw_gps_route,
                color="#fca5a5",
                weight=2,
                opacity=0.75,
                dash_array="8, 8",
                tooltip="Roh-GPS vor Weg-Matching",
            ).add_to(route_group)

    if len(gps_route) >= 2:
        gps_line = folium.PolyLine(
            locations=gps_route,
            color="#dc2626",
            weight=4,
            opacity=0.9,
            tooltip="Realer GPS-Laufweg",
        )
        gps_line.add_to(route_group)
        PolyLineTextPath(
            gps_line,
            ">",
            repeat=True,
            offset=8,
            attributes={"fill": "#dc2626", "font-weight": "bold", "font-size": "13"},
        ).add_to(route_group)

    if len(wifi_route) >= 2:
        wifi_line = folium.PolyLine(
            locations=wifi_route,
            color="#2563eb",
            weight=4,
            opacity=0.9,
            tooltip="Geschaetzter WLAN-Laufweg",
        )
        wifi_line.add_to(route_group)
        PolyLineTextPath(
            wifi_line,
            ">",
            repeat=True,
            offset=8,
            attributes={"fill": "#2563eb", "font-weight": "bold", "font-size": "13"},
        ).add_to(route_group)

    for _, row in valid_rows.iterrows():
        wifi_quality_color = _route_quality_color(float(row["error_m"]))
        folium.CircleMarker(
            location=[row["actual_latitude"], row["actual_longitude"]],
            radius=3,
            color="#991b1b",
            fill=True,
            fill_color="#ffffff",
            fill_opacity=1.0,
            weight=2,
            tooltip=f"GPS {row['scan_id']}",
            popup=folium.Popup(f"GPS-Punkt<br>Scan: {row['scan_id']}", max_width=220),
        ).add_to(route_group)

        folium.CircleMarker(
            location=[row["estimated_latitude"], row["estimated_longitude"]],
            radius=4,
            color=wifi_quality_color,
            fill=True,
            fill_color=wifi_quality_color,
            fill_opacity=0.9,
            weight=2,
            tooltip=f"WLAN {row['scan_id']}",
            popup=folium.Popup(
                f"WLAN-Schaetzung<br>Scan: {row['scan_id']}"
                f"<br>Fehler: {row['error_m']:.1f} m"
                f"<br>AP-Treffer: {int(row['matched_access_points'])}"
                f"<br>Methode: {row.get('method', '-')}",
                max_width=260,
            ),
        ).add_to(route_group)

        error_line = folium.PolyLine(
            locations=[
                [row["actual_latitude"], row["actual_longitude"]],
                [row["estimated_latitude"], row["estimated_longitude"]],
            ],
            color="#f97316",
            weight=2,
            opacity=0.65,
            dash_array="6, 8",
            tooltip=f"Abweichung {row['error_m']:.1f} m",
        )
        error_line.add_to(route_group)

    route_group.add_to(route_map)


def _route_quality_color(error_m: float) -> str:
    if error_m <= 20:
        return "#16a34a"
    if error_m <= 50:
        return "#2563eb"
    if error_m <= 100:
        return "#f97316"
    return "#dc2626"


def _sample_route_detail_rows(route_rows: pd.DataFrame, max_points: int = MAX_ROUTE_DETAIL_POINTS) -> pd.DataFrame:
    if len(route_rows) <= max_points:
        return route_rows

    step = max(1, len(route_rows) // max_points)
    sampled = route_rows.iloc[::step].copy()
    last_row = route_rows.tail(1)
    if sampled.iloc[-1]["scan_id"] != last_row.iloc[0]["scan_id"]:
        sampled = pd.concat([sampled, last_row], ignore_index=True)
    return sampled


def fit_map_to_bounds(
    router_map: folium.Map,
    scan_summary: pd.DataFrame,
    access_points: pd.DataFrame,
    osm_bounds: dict[str, float],
    route_comparison: pd.DataFrame | None = None,
) -> None:
    frames = []
    if {"latitude", "longitude"}.issubset(scan_summary.columns):
        frames.append(scan_summary.loc[:, ["latitude", "longitude"]].dropna())
    if {"latitude", "longitude"}.issubset(access_points.columns):
        frames.append(access_points.loc[:, ["latitude", "longitude"]].dropna())
    if route_comparison is not None and not route_comparison.empty:
        actual_positions = route_comparison.loc[:, ["actual_latitude", "actual_longitude"]].rename(
            columns={"actual_latitude": "latitude", "actual_longitude": "longitude"}
        )
        estimated_positions = route_comparison.loc[:, ["estimated_latitude", "estimated_longitude"]].rename(
            columns={"estimated_latitude": "latitude", "estimated_longitude": "longitude"}
        )
        frames.extend([actual_positions.dropna(), estimated_positions.dropna()])

    if frames:
        positions = pd.concat(frames, ignore_index=True)
        min_lat = float(positions["latitude"].min())
        max_lat = float(positions["latitude"].max())
        min_lon = float(positions["longitude"].min())
        max_lon = float(positions["longitude"].max())
    else:
        min_lat = float(osm_bounds["minlat"])
        max_lat = float(osm_bounds["maxlat"])
        min_lon = float(osm_bounds["minlon"])
        max_lon = float(osm_bounds["maxlon"])

    lat_padding = max((max_lat - min_lat) * 0.8, 0.00025)
    lon_padding = max((max_lon - min_lon) * 0.18, 0.00018)

    router_map.fit_bounds(
        [
            [min_lat - lat_padding, min_lon - lon_padding],
            [max_lat + lat_padding, max_lon + lon_padding],
        ]
    )


def _get_map_center(
    scan_summary: pd.DataFrame,
    access_points: pd.DataFrame,
    osm_bounds: dict[str, float],
) -> tuple[float, float]:
    scan_positions = scan_summary.dropna(subset=["latitude", "longitude"]) if {"latitude", "longitude"}.issubset(scan_summary.columns) else pd.DataFrame()
    valid_access_points = access_points.dropna(subset=["latitude", "longitude"]) if {"latitude", "longitude"}.issubset(access_points.columns) else pd.DataFrame()

    if not scan_positions.empty:
        return float(scan_positions["latitude"].mean()), float(scan_positions["longitude"].mean())
    if not valid_access_points.empty:
        return float(valid_access_points["latitude"].mean()), float(valid_access_points["longitude"].mean())

    return (
        (float(osm_bounds["minlat"]) + float(osm_bounds["maxlat"])) / 2,
        (float(osm_bounds["minlon"]) + float(osm_bounds["maxlon"])) / 2,
    )


def _get_simple_map_center(
    position_estimate: dict[str, object] | None,
    osm_bounds: dict[str, float],
) -> tuple[float, float]:
    if position_estimate is not None:
        return float(position_estimate["latitude"]), float(position_estimate["longitude"])

    return (
        (float(osm_bounds["minlat"]) + float(osm_bounds["maxlat"])) / 2,
        (float(osm_bounds["minlon"]) + float(osm_bounds["maxlon"])) / 2,
    )


def _get_router_estimation_center(
    selected_observations: pd.DataFrame,
    router_estimates: pd.DataFrame,
    osm_bounds: dict[str, float],
) -> tuple[float, float]:
    valid_routers = router_estimates.dropna(subset=["latitude", "longitude"]) if not router_estimates.empty else pd.DataFrame()
    valid_observations = (
        selected_observations.dropna(subset=["latitude", "longitude"])
        if not selected_observations.empty
        else pd.DataFrame()
    )

    if not valid_routers.empty:
        return float(valid_routers["latitude"].mean()), float(valid_routers["longitude"].mean())
    if not valid_observations.empty:
        return float(valid_observations["latitude"].mean()), float(valid_observations["longitude"].mean())

    return (
        (float(osm_bounds["minlat"]) + float(osm_bounds["maxlat"])) / 2,
        (float(osm_bounds["minlon"]) + float(osm_bounds["maxlon"])) / 2,
    )


def _get_route_estimation_center(
    route_estimates: pd.DataFrame,
    osm_bounds: dict[str, float],
) -> tuple[float, float]:
    if not route_estimates.empty:
        latitude_columns = [column for column in ["actual_latitude", "estimated_latitude"] if column in route_estimates]
        longitude_columns = [column for column in ["actual_longitude", "estimated_longitude"] if column in route_estimates]
        latitudes = pd.concat([route_estimates[column] for column in latitude_columns], ignore_index=True).dropna()
        longitudes = pd.concat([route_estimates[column] for column in longitude_columns], ignore_index=True).dropna()
        if not latitudes.empty and not longitudes.empty:
            return float(latitudes.mean()), float(longitudes.mean())

    return (
        (float(osm_bounds["minlat"]) + float(osm_bounds["maxlat"])) / 2,
        (float(osm_bounds["minlon"]) + float(osm_bounds["maxlon"])) / 2,
    )


def fit_route_estimation_map(
    route_map: folium.Map,
    route_estimates: pd.DataFrame,
    osm_bounds: dict[str, float],
) -> None:
    if route_estimates.empty:
        route_map.fit_bounds(
            [
                [float(osm_bounds["minlat"]), float(osm_bounds["minlon"])],
                [float(osm_bounds["maxlat"]), float(osm_bounds["maxlon"])],
            ]
        )
        return

    positions = pd.DataFrame(
        {
            "latitude": pd.concat(
                [route_estimates["actual_latitude"], route_estimates["estimated_latitude"]],
                ignore_index=True,
            ),
            "longitude": pd.concat(
                [route_estimates["actual_longitude"], route_estimates["estimated_longitude"]],
                ignore_index=True,
            ),
        }
    ).dropna()

    if positions.empty:
        return

    min_lat = float(positions["latitude"].min())
    max_lat = float(positions["latitude"].max())
    min_lon = float(positions["longitude"].min())
    max_lon = float(positions["longitude"].max())
    lat_padding = max((max_lat - min_lat) * 0.25, 0.00035)
    lon_padding = max((max_lon - min_lon) * 0.25, 0.00035)
    route_map.fit_bounds(
        [
            [min_lat - lat_padding, min_lon - lon_padding],
            [max_lat + lat_padding, max_lon + lon_padding],
        ]
    )


def fit_router_estimation_map(
    router_map: folium.Map,
    selected_observations: pd.DataFrame,
    router_estimates: pd.DataFrame,
    osm_bounds: dict[str, float],
) -> None:
    frames = []
    if not selected_observations.empty and {"latitude", "longitude"}.issubset(selected_observations.columns):
        frames.append(selected_observations.loc[:, ["latitude", "longitude"]].dropna())
    if not router_estimates.empty and {"latitude", "longitude"}.issubset(router_estimates.columns):
        frames.append(router_estimates.loc[:, ["latitude", "longitude"]].dropna())

    if not frames:
        router_map.fit_bounds(
            [
                [float(osm_bounds["minlat"]), float(osm_bounds["minlon"])],
                [float(osm_bounds["maxlat"]), float(osm_bounds["maxlon"])],
            ]
        )
        return

    positions = pd.concat(frames, ignore_index=True)
    min_lat = float(positions["latitude"].min())
    max_lat = float(positions["latitude"].max())
    min_lon = float(positions["longitude"].min())
    max_lon = float(positions["longitude"].max())
    lat_padding = max((max_lat - min_lat) * 0.45, 0.00025)
    lon_padding = max((max_lon - min_lon) * 0.45, 0.00025)

    router_map.fit_bounds(
        [
            [min_lat - lat_padding, min_lon - lon_padding],
            [max_lat + lat_padding, max_lon + lon_padding],
        ]
    )


def fit_simple_map_to_position(
    location_map: folium.Map,
    position_estimate: dict[str, object] | None,
    osm_bounds: dict[str, float],
) -> None:
    if position_estimate is None:
        location_map.fit_bounds(
            [
                [float(osm_bounds["minlat"]), float(osm_bounds["minlon"])],
                [float(osm_bounds["maxlat"]), float(osm_bounds["maxlon"])],
            ]
        )
        return

    latitude = float(position_estimate["latitude"])
    longitude = float(position_estimate["longitude"])
    raw_latitude = float(position_estimate["raw_latitude"])
    raw_longitude = float(position_estimate["raw_longitude"])
    padding = 0.00045
    location_map.fit_bounds(
        [
            [min(latitude, raw_latitude) - padding, min(longitude, raw_longitude) - padding],
            [max(latitude, raw_latitude) + padding, max(longitude, raw_longitude) + padding],
        ]
    )

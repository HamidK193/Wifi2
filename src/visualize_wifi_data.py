from pathlib import Path
from xml.etree import ElementTree as ET

import folium
import pandas as pd


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

        if "highway" in tags:
            highways.append(coordinates)

        if "building" in tags and len(coordinates) >= 3:
            polygon = coordinates
            if polygon[0] != polygon[-1]:
                polygon = polygon + [polygon[0]]
            buildings.append(polygon)

    return {
        "bounds": bounds,
        "highways": highways,
        "buildings": buildings,
    }


def build_router_map(
    osm_map: dict[str, object],
    scan_summary: pd.DataFrame,
    selected_observations: pd.DataFrame,
    overlap_points: pd.DataFrame,
    network_colors: dict[str, str],
    access_points: pd.DataFrame,
    position_estimate: object | None = None,
) -> folium.Map:
    center_lat, center_lon = _get_map_center(scan_summary, access_points, osm_map["bounds"])

    router_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=18,
        tiles=None,
        control_scale=True,
    )

    add_osm_base_layers(router_map, osm_map)
    add_scan_markers(router_map, scan_summary)
    add_access_point_markers(router_map, access_points)
    add_router_radius_circles(router_map, selected_observations, network_colors)
    add_overlap_markers(router_map, overlap_points)
    add_position_estimate_marker(router_map, position_estimate)
    fit_map_to_bounds(router_map, scan_summary, access_points, osm_map["bounds"])
    folium.LayerControl(collapsed=False).add_to(router_map)

    return router_map


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


def fit_map_to_bounds(
    router_map: folium.Map,
    scan_summary: pd.DataFrame,
    access_points: pd.DataFrame,
    osm_bounds: dict[str, float],
) -> None:
    frames = []
    if {"latitude", "longitude"}.issubset(scan_summary.columns):
        frames.append(scan_summary.loc[:, ["latitude", "longitude"]].dropna())
    if {"latitude", "longitude"}.issubset(access_points.columns):
        frames.append(access_points.loc[:, ["latitude", "longitude"]].dropna())

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

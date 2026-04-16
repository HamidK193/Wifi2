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
    position_estimate: object | None = None,
) -> folium.Map:
    center_lat = float(scan_summary["latitude"].mean())
    center_lon = float(scan_summary["longitude"].mean())

    router_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=18,
        tiles=None,
        control_scale=True,
    )

    add_osm_base_layers(router_map, osm_map)
    add_scan_markers(router_map, scan_summary)
    add_router_radius_circles(router_map, selected_observations, network_colors)
    add_overlap_markers(router_map, overlap_points)
    add_position_estimate_marker(router_map, position_estimate)
    fit_map_to_scan_bounds(router_map, scan_summary)
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
    scan_group = folium.FeatureGroup(name="Messpunkte", show=True)

    for _, row in scan_summary.iterrows():
        popup_text = (
            f"Scan: {row['scan_id']}<br>"
            f"Zeit: {row['timestamp']}<br>"
            f"Sichtbare Netzwerke: {int(row['visible_networks'])}<br>"
            f"Mittlere RSSI: {row['mean_rssi']:.1f} dBm<br>"
            f"GPS-Genauigkeit: {row['accuracy_m']:.1f} m"
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
            tooltip=row["scan_id"],
        ).add_to(scan_group)

    scan_group.add_to(router_map)


def add_router_radius_circles(
    router_map: folium.Map,
    selected_observations: pd.DataFrame,
    network_colors: dict[str, str],
) -> None:
    radius_group = folium.FeatureGroup(name="Moegliche Router-Radien", show=True)

    for _, row in selected_observations.iterrows():
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
        f"Verwendete Treffer: {position_estimate['matched_networks']}<br>"
        f"Bestes RSSI-RMSE: {position_estimate['best_rmse']:.1f}"
    )
    if position_estimate["error_m"] is not None:
        popup_text += f"<br>Fehler gegen Testpunkt: {position_estimate['error_m']:.1f} m"

    folium.Marker(
        location=[position_estimate["latitude"], position_estimate["longitude"]],
        popup=folium.Popup(popup_text, max_width=260),
        tooltip="Geschaetzter Standort",
        icon=folium.Icon(color="red", icon="screenshot", prefix="glyphicon"),
    ).add_to(estimate_group)

    if position_estimate["actual_latitude"] is not None and position_estimate["actual_longitude"] is not None:
        folium.Marker(
            location=[position_estimate["actual_latitude"], position_estimate["actual_longitude"]],
            popup=folium.Popup("Tatsaechlicher Test-Scan", max_width=220),
            tooltip="Tatsaechlicher Test-Scan",
            icon=folium.Icon(color="green", icon="map-marker", prefix="glyphicon"),
        ).add_to(estimate_group)

    estimate_group.add_to(router_map)


def fit_map_to_scan_bounds(router_map: folium.Map, scan_summary: pd.DataFrame) -> None:
    min_lat = float(scan_summary["latitude"].min())
    max_lat = float(scan_summary["latitude"].max())
    min_lon = float(scan_summary["longitude"].min())
    max_lon = float(scan_summary["longitude"].max())

    lat_padding = max((max_lat - min_lat) * 0.8, 0.00025)
    lon_padding = max((max_lon - min_lon) * 0.18, 0.00018)

    router_map.fit_bounds(
        [
            [min_lat - lat_padding, min_lon - lon_padding],
            [max_lat + lat_padding, max_lon + lon_padding],
        ]
    )

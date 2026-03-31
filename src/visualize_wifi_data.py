import math
from pathlib import Path
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
import pandas as pd


def create_visualizations(
    cleaned_dataframe: pd.DataFrame,
    scan_summary: pd.DataFrame,
    output_dir: str | Path,
) -> list[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    created_files = [
        plot_scan_positions(scan_summary, output_path / "scan_positions.png"),
        plot_top_ssids(cleaned_dataframe, output_path / "top_ssids.png"),
        plot_rssi_distribution(cleaned_dataframe, output_path / "rssi_distribution.png"),
    ]

    return created_files


def create_osm_visualizations(
    scan_summary: pd.DataFrame,
    osm_path: str | Path,
    output_dir: str | Path,
) -> list[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    osm_map = load_osm_map(osm_path)

    return [
        plot_osm_scan_map(
            scan_summary,
            osm_map,
            value_column="visible_networks",
            colorbar_label="Sichtbare Netzwerke",
            title="WiFi-Scans auf OpenStreetMap (sichtbare Netzwerke)",
            output_path=output_path / "osm_scans_visible_networks.png",
            cmap="viridis",
        ),
        plot_osm_scan_map(
            scan_summary,
            osm_map,
            value_column="mean_rssi",
            colorbar_label="Mittlere RSSI (dBm)",
            title="WiFi-Scans auf OpenStreetMap (mittlere RSSI)",
            output_path=output_path / "osm_scans_mean_rssi.png",
            cmap="plasma",
        ),
    ]


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
            node_coordinates[node_id] = (float(lon), float(lat))

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


def plot_osm_scan_map(
    scan_summary: pd.DataFrame,
    osm_map: dict[str, object],
    value_column: str,
    colorbar_label: str,
    title: str,
    output_path: str | Path,
    cmap: str,
) -> Path:
    path = Path(output_path)
    highways = osm_map["highways"]
    buildings = osm_map["buildings"]
    plot_bounds = get_zoomed_plot_bounds(scan_summary, osm_map["bounds"])

    figure, axis = plt.subplots(figsize=(12, 9))
    axis.set_facecolor("#f8fafc")

    if buildings:
        building_collection = PolyCollection(
            buildings,
            facecolors="#e5e7eb",
            edgecolors="#d1d5db",
            linewidths=0.3,
            zorder=1,
        )
        axis.add_collection(building_collection)

    if highways:
        highway_collection = LineCollection(
            highways,
            colors="#6b7280",
            linewidths=0.8,
            alpha=0.8,
            zorder=2,
        )
        axis.add_collection(highway_collection)

    scatter = axis.scatter(
        scan_summary["longitude"],
        scan_summary["latitude"],
        c=scan_summary[value_column],
        cmap=cmap,
        edgecolors="black",
        linewidths=0.5,
        s=170,
        zorder=3,
    )

    for _, row in scan_summary.iterrows():
        axis.annotate(
            row["scan_id"],
            (row["longitude"], row["latitude"]),
            textcoords="offset points",
            xytext=(4, 4),
            fontsize=8,
            zorder=4,
        )

    axis.set_xlim(plot_bounds["minlon"], plot_bounds["maxlon"])
    axis.set_ylim(plot_bounds["minlat"], plot_bounds["maxlat"])
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    axis.set_title(title)

    axis.text(
        0.99,
        0.01,
        "(c) OpenStreetMap contributors",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#4b5563",
    )

    figure.colorbar(scatter, ax=axis, label=colorbar_label)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)

    return path


def get_zoomed_plot_bounds(
    scan_summary: pd.DataFrame,
    osm_bounds: dict[str, float],
) -> dict[str, float]:
    min_lat = float(scan_summary["latitude"].min())
    max_lat = float(scan_summary["latitude"].max())
    min_lon = float(scan_summary["longitude"].min())
    max_lon = float(scan_summary["longitude"].max())

    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    mean_latitude = (min_lat + max_lat) / 2

    lon_padding = max(lon_span * 0.12, 0.00010)
    padded_lon_span = lon_span + 2 * lon_padding

    # Make the visible map height match the visible width more closely,
    # so the route is not flattened into a thin strip.
    target_lat_span = max(
        lat_span + 0.00040,
        (padded_lon_span * math.cos(math.radians(mean_latitude))) * 0.75,
    )
    lat_padding = max((target_lat_span - lat_span) / 2, 0.00020)

    return {
        "minlat": max(osm_bounds["minlat"], min_lat - lat_padding),
        "maxlat": min(osm_bounds["maxlat"], max_lat + lat_padding),
        "minlon": max(osm_bounds["minlon"], min_lon - lon_padding),
        "maxlon": min(osm_bounds["maxlon"], max_lon + lon_padding),
    }


def plot_scan_positions(scan_summary: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)

    plt.figure(figsize=(10, 5))
    scatter = plt.scatter(
        scan_summary["longitude"],
        scan_summary["latitude"],
        c=scan_summary["visible_networks"],
        cmap="viridis",
        s=90,
    )

    for _, row in scan_summary.iterrows():
        plt.annotate(
            row["scan_id"],
            (row["longitude"], row["latitude"]),
            textcoords="offset points",
            xytext=(4, 4),
            fontsize=8,
        )

    plt.colorbar(scatter, label="Sichtbare Netzwerke")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("WiFi-Messpunkte")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

    return path


def plot_top_ssids(
    cleaned_dataframe: pd.DataFrame,
    output_path: str | Path,
    top_n: int = 10,
) -> Path:
    path = Path(output_path)
    ssid_counts = cleaned_dataframe["ssid"].value_counts().head(top_n)

    plt.figure(figsize=(10, 5))
    ssid_counts.sort_values().plot(kind="barh", color="#3b82f6")
    plt.xlabel("Anzahl Messungen")
    plt.ylabel("SSID")
    plt.title(f"Hauefigste SSIDs (Top {top_n})")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

    return path


def plot_rssi_distribution(cleaned_dataframe: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)

    plt.figure(figsize=(10, 5))
    plt.hist(cleaned_dataframe["rssi"], bins=15, color="#10b981", edgecolor="black")
    plt.xlabel("RSSI (dBm)")
    plt.ylabel("Anzahl Messungen")
    plt.title("RSSI-Verteilung")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

    return path

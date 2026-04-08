from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.localization_logic import estimate_overlap_points
from src.project_pipeline import run_data_pipeline
from src.visualize_wifi_data import build_router_map, load_osm_map

RAW_CSV_PATH = Path("data/raw/WigleWifi_20260408161721.csv")
RAW_OSM_PATH = Path("data/raw/map_innenstadt.osm")
PROCESSED_DIR = Path("data/processed")
ALL_OPTION = "Alle"


@st.cache_data(show_spinner=False)
def load_pipeline_data() -> dict[str, object]:
    return run_data_pipeline(RAW_CSV_PATH, PROCESSED_DIR)


@st.cache_data(show_spinner=False)
def load_osm_data() -> dict[str, object]:
    return load_osm_map(RAW_OSM_PATH)


def main() -> None:
    st.set_page_config(page_title="WiFi Selbstlokalisierung", layout="wide")
    st.title("WiFi-basierte Selbstlokalisierung")
    st.write(
        "Die Karte zeigt nicht den exakten Routerpunkt, sondern pro Beobachtung "
        "einen moeglichen Radiusbereich. Mehrere Kreise desselben Netzwerks "
        "koennen sich ueberlagern und damit den wahrscheinlichen Routerbereich eingrenzen."
    )

    if not RAW_CSV_PATH.exists():
        st.error(f"CSV-Datei fehlt: {RAW_CSV_PATH}")
        return

    if not RAW_OSM_PATH.exists():
        st.error(f"OSM-Datei fehlt: {RAW_OSM_PATH}")
        return

    pipeline_data = load_pipeline_data()
    osm_map = load_osm_data()

    scan_summary = pipeline_data["scan_summary"]
    network_summary = pipeline_data["network_summary"]
    network_observations = pipeline_data["network_observations"]
    dataset_summary = pipeline_data["dataset_summary"]

    selected_ssid, selected_bssid = render_filters(network_summary)
    filtered_summary = filter_network_summary(network_summary, selected_ssid, selected_bssid)
    filtered_observations = filter_network_observations(network_observations, selected_ssid, selected_bssid)
    network_colors = build_network_colors(filtered_summary["network_id"].tolist())
    overlap_points = build_overlap_points(filtered_summary, filtered_observations, network_colors)

    router_map = build_router_map(
        osm_map,
        scan_summary,
        filtered_observations,
        overlap_points,
        network_colors,
    )

    left_column, right_column = st.columns([2.4, 1])

    with left_column:
        st.subheader("Interaktive Karte")
        st_folium(router_map, use_container_width=True, height=780)

    with right_column:
        render_sidebar_content(
            dataset_summary,
            filtered_summary,
            filtered_observations,
            overlap_points,
            network_colors,
        )


def render_filters(network_summary: pd.DataFrame) -> tuple[str, str]:
    with st.sidebar:
        st.header("Filter")

        ssid_options = [ALL_OPTION] + sorted(network_summary["ssid"].dropna().unique().tolist())
        selected_ssid = st.selectbox("SSID", ssid_options, index=0)

        bssid_options = get_bssid_options(network_summary, selected_ssid)
        selected_bssid = st.selectbox("MAC-Adresse (BSSID)", bssid_options, index=0)

    return selected_ssid, selected_bssid


def get_bssid_options(network_summary: pd.DataFrame, selected_ssid: str) -> list[str]:
    if selected_ssid == ALL_OPTION:
        bssid_values = sorted(network_summary["bssid"].dropna().unique().tolist())
    else:
        bssid_values = sorted(
            network_summary.loc[network_summary["ssid"] == selected_ssid, "bssid"]
            .dropna()
            .unique()
            .tolist()
        )

    return [ALL_OPTION] + bssid_values


def filter_network_summary(
    network_summary: pd.DataFrame,
    selected_ssid: str,
    selected_bssid: str,
) -> pd.DataFrame:
    filtered = network_summary.copy()

    if selected_ssid != ALL_OPTION:
        filtered = filtered.loc[filtered["ssid"] == selected_ssid]

    if selected_bssid != ALL_OPTION:
        filtered = filtered.loc[filtered["bssid"] == selected_bssid]

    return filtered.reset_index(drop=True)


def filter_network_observations(
    network_observations: pd.DataFrame,
    selected_ssid: str,
    selected_bssid: str,
) -> pd.DataFrame:
    filtered = network_observations.copy()

    if selected_ssid != ALL_OPTION:
        filtered = filtered.loc[filtered["ssid"] == selected_ssid]

    if selected_bssid != ALL_OPTION:
        filtered = filtered.loc[filtered["bssid"] == selected_bssid]

    return filtered.reset_index(drop=True)


def build_network_colors(network_ids: list[str]) -> dict[str, str]:
    palette = [
        "#2563eb",
        "#dc2626",
        "#16a34a",
        "#ca8a04",
        "#9333ea",
        "#0891b2",
        "#ea580c",
        "#4f46e5",
        "#be123c",
        "#0f766e",
    ]

    return {
        network_id: palette[index % len(palette)]
        for index, network_id in enumerate(network_ids)
    }


def build_overlap_points(
    filtered_summary: pd.DataFrame,
    filtered_observations: pd.DataFrame,
    network_colors: dict[str, str],
) -> pd.DataFrame:
    overlap_frames: list[pd.DataFrame] = []

    for _, summary_row in filtered_summary.iterrows():
        network_id = summary_row["network_id"]
        network_rows = filtered_observations.loc[filtered_observations["network_id"] == network_id]
        overlap_points = estimate_overlap_points(network_rows)

        if overlap_points.empty:
            continue

        overlap_points = overlap_points.copy()
        overlap_points["network_id"] = network_id
        overlap_points["ssid"] = summary_row["ssid"]
        overlap_points["bssid"] = summary_row["bssid"]
        overlap_points["color"] = network_colors[network_id]
        overlap_frames.append(overlap_points)

    if not overlap_frames:
        return pd.DataFrame(columns=["latitude", "longitude", "support_count", "network_id", "ssid", "bssid", "color"])

    return pd.concat(overlap_frames, ignore_index=True)


def render_sidebar_content(
    dataset_summary: dict[str, object],
    filtered_summary: pd.DataFrame,
    filtered_observations: pd.DataFrame,
    overlap_points: pd.DataFrame,
    network_colors: dict[str, str],
) -> None:
    st.subheader("Datensatz")
    st.metric("Scans", int(dataset_summary["scans"]))
    st.metric("Gefilterte Netzwerke", int(filtered_summary["network_id"].nunique()))
    st.metric("Messzeilen", int(dataset_summary["rows"]))

    st.subheader("Gefilterte Auswahl")
    if filtered_summary.empty:
        st.warning("Mit dieser Filterkombination wurden keine Netzwerke gefunden.")
        return

    if len(filtered_summary) == 1:
        selected_summary = filtered_summary.iloc[0]
        st.write(f"SSID: `{selected_summary['ssid']}`")
        st.write(f"BSSID: `{selected_summary['bssid']}`")
        st.write(f"Beobachtete Scans: {int(selected_summary['scan_count'])}")
        st.write(f"Gesamtbeobachtungen: {int(selected_summary['total_observations'])}")
        st.write(f"Mittlere RSSI: {selected_summary['mean_rssi']:.1f} dBm")
        st.write(
            "Radiusbereich: "
            f"{selected_summary['min_radius_m']:.1f} m bis {selected_summary['max_radius_m']:.1f} m"
        )
        st.write(
            "Ueberlappungspunkte: "
            f"{len(overlap_points)}"
        )
    else:
        st.write(
            "Mehrere Netzwerke sind aktiv. Jede eindeutige Kombination aus "
            "`SSID + BSSID` wird in einer eigenen Farbe dargestellt."
        )

    st.subheader("Farben der Netzwerke")
    color_rows = filtered_summary.loc[:, ["ssid", "bssid", "network_id"]].copy()
    color_rows["farbe"] = color_rows["network_id"].map(network_colors)
    st.dataframe(color_rows, use_container_width=True, hide_index=True)

    st.subheader("Beobachtungen")
    st.dataframe(
        filtered_observations[
            [
                "scan_id",
                "ssid",
                "bssid",
                "mean_rssi",
                "estimated_radius_m",
                "observation_count",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    if overlap_points.empty:
        st.info(
            "Fuer die aktuelle Auswahl gibt es noch keine starke Kreis-Ueberlappung "
            "aus mindestens zwei Beobachtungen desselben Netzwerks."
        )
    else:
        st.success(
            "Es wurden Ueberlappungspunkte gefunden. Diese markieren Bereiche, "
            "in denen mehrere Radiuskreise desselben Netzwerks zusammenlaufen."
        )
        st.dataframe(
            overlap_points[
                ["ssid", "bssid", "support_count", "latitude", "longitude"]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Architekturhinweis")
    st.write(
        "Die Software modelliert pro Messung nur einen moeglichen Radius. "
        "Ein exakter Routerstandort wird nicht behauptet. Erst mehrere Beobachtungen "
        "desselben Netzwerks koennen einen wahrscheinlicheren Bereich ergeben."
    )


if __name__ == "__main__":
    main()

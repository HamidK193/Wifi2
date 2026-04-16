from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.fingerprint_localization import (
    estimate_position_from_fingerprint,
    get_scan_input_observations,
    parse_manual_wifi_input,
)
from src.localization_logic import estimate_overlap_points
from src.project_pipeline import run_data_pipeline
from src.visualize_wifi_data import build_router_map, load_osm_map

RAW_CSV_PATH = Path("data/raw/WigleWifi_20260408161721.csv")
RAW_OSM_PATH = Path("data/raw/map_innenstadt.osm")
PROCESSED_DIR = Path("data/processed")
ALL_OPTION = "Alle"
MAX_RADIUS_OBSERVATIONS = 1000
OVERLAP_COLUMNS = ["latitude", "longitude", "support_count", "network_id", "ssid", "bssid", "color"]


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

    with st.spinner("Daten werden geladen..."):
        pipeline_data = load_pipeline_data()
        osm_map = load_osm_data()

    scan_summary = pipeline_data["scan_summary"]
    cleaned_dataframe = pipeline_data["cleaned_dataframe"]
    network_summary = pipeline_data["network_summary"]
    network_observations = pipeline_data["network_observations"]
    dataset_summary = pipeline_data["dataset_summary"]

    selected_ssid, selected_bssid = render_filters(network_summary)
    position_estimate, test_input_observations = render_position_test_controls(
        cleaned_dataframe,
        scan_summary,
    )
    filtered_summary = filter_network_summary(network_summary, selected_ssid, selected_bssid)
    filtered_observations = filter_network_observations(network_observations, selected_ssid, selected_bssid)
    map_observations = get_map_observations(filtered_observations, selected_ssid, selected_bssid)
    network_colors = build_network_colors(filtered_summary["network_id"].tolist())
    if should_calculate_overlap(filtered_summary, selected_ssid, selected_bssid):
        overlap_points = build_overlap_points(filtered_summary, map_observations, network_colors)
    else:
        overlap_points = pd.DataFrame(columns=OVERLAP_COLUMNS)

    with st.spinner("Karte wird aufgebaut..."):
        router_map = build_router_map(
            osm_map,
            scan_summary,
            map_observations,
            overlap_points,
            network_colors,
            position_estimate,
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
            map_observations,
            overlap_points,
            network_colors,
            selected_ssid,
            selected_bssid,
            position_estimate,
            test_input_observations,
        )


def render_filters(network_summary: pd.DataFrame) -> tuple[str, str]:
    with st.sidebar:
        st.header("Filter")

        ssid_options = [ALL_OPTION] + sorted(network_summary["ssid"].dropna().unique().tolist())
        selected_ssid = st.selectbox("SSID", ssid_options, index=0)

        bssid_options = get_bssid_options(network_summary, selected_ssid)
        selected_bssid = st.selectbox("MAC-Adresse (BSSID)", bssid_options, index=0)

    return selected_ssid, selected_bssid


def render_position_test_controls(
    cleaned_dataframe: pd.DataFrame,
    scan_summary: pd.DataFrame,
) -> tuple[object | None, pd.DataFrame]:
    with st.sidebar:
        st.header("Standort-Test")
        mode = st.selectbox(
            "Eingabe",
            ["Aus", "Vorhandenen Scan testen", "Manuelle Eingabe"],
            index=0,
        )
        k = st.slider("Vergleichspunkte (k)", min_value=1, max_value=5, value=3)

        if mode == "Aus":
            return None, pd.DataFrame(columns=["network_id", "ssid", "bssid", "rssi"])

        if mode == "Vorhandenen Scan testen":
            scan_ids = scan_summary["scan_id"].tolist()
            selected_scan_id = st.selectbox("Test-Scan", scan_ids, index=0)
            input_observations = get_scan_input_observations(cleaned_dataframe, selected_scan_id)
            estimate = estimate_position_from_fingerprint(
                cleaned_dataframe,
                input_observations,
                exclude_scan_id=selected_scan_id,
                k=k,
            )
            return estimate, input_observations

        manual_text = st.text_area(
            "WLAN-Werte",
            placeholder="SSID,BSSID,RSSI\nPF-NET,aa:bb:cc:dd:ee:ff,-65",
            height=140,
        )
        input_observations = parse_manual_wifi_input(manual_text)
        estimate = estimate_position_from_fingerprint(
            cleaned_dataframe,
            input_observations,
            k=k,
        )
        return estimate, input_observations


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


def should_show_radius_circles(
    selected_ssid: str,
    selected_bssid: str,
    observation_count: int,
) -> bool:
    if selected_ssid == ALL_OPTION and selected_bssid == ALL_OPTION:
        return False

    return observation_count <= MAX_RADIUS_OBSERVATIONS


def should_calculate_overlap(
    filtered_summary: pd.DataFrame,
    selected_ssid: str,
    selected_bssid: str,
) -> bool:
    return (
        selected_ssid != ALL_OPTION
        and selected_bssid != ALL_OPTION
        and len(filtered_summary) == 1
    )


def get_map_observations(
    filtered_observations: pd.DataFrame,
    selected_ssid: str,
    selected_bssid: str,
) -> pd.DataFrame:
    if not should_show_radius_circles(selected_ssid, selected_bssid, len(filtered_observations)):
        return filtered_observations.iloc[0:0].copy()

    return filtered_observations


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
    if len(filtered_summary) != 1:
        return pd.DataFrame(columns=OVERLAP_COLUMNS)

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
        return pd.DataFrame(columns=OVERLAP_COLUMNS)

    return pd.concat(overlap_frames, ignore_index=True)


def render_sidebar_content(
    dataset_summary: dict[str, object],
    filtered_summary: pd.DataFrame,
    filtered_observations: pd.DataFrame,
    map_observations: pd.DataFrame,
    overlap_points: pd.DataFrame,
    network_colors: dict[str, str],
    selected_ssid: str,
    selected_bssid: str,
    position_estimate: object | None,
    test_input_observations: pd.DataFrame,
) -> None:
    st.subheader("Datensatz")
    st.metric("Scans", int(dataset_summary["scans"]))
    st.metric("Gefilterte Netzwerke", int(filtered_summary["network_id"].nunique()))
    st.metric("Messzeilen", int(dataset_summary["rows"]))

    st.subheader("Gefilterte Auswahl")
    if filtered_summary.empty:
        st.warning("Mit dieser Filterkombination wurden keine Netzwerke gefunden.")
        return

    if selected_ssid == ALL_OPTION and selected_bssid == ALL_OPTION:
        st.info(
            "Uebersicht: Es werden nur die Messpunkte angezeigt. "
            "Waehle eine SSID oder MAC-Adresse aus, um Router-Radien einzublenden."
        )
        render_top_networks(filtered_summary)
        render_position_estimate(position_estimate, test_input_observations)
        render_architecture_note()
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
        if map_observations.empty and len(filtered_observations) > MAX_RADIUS_OBSERVATIONS:
            st.warning(
                "Die aktuelle Auswahl enthaelt zu viele Radiuskreise. "
                "Bitte waehle zusaetzlich eine MAC-Adresse aus."
            )
        elif overlap_points.empty:
            st.info(
                "Bei mehreren Netzwerken wird keine globale Kreis-Ueberlappung berechnet. "
                "Waehle eine konkrete MAC-Adresse aus, um Schnittbereiche zu sehen."
            )

    st.subheader("Farben der Netzwerke")
    color_rows = filtered_summary.loc[:, ["ssid", "bssid", "network_id"]].copy()
    color_rows["farbe"] = color_rows["network_id"].map(network_colors)
    st.dataframe(color_rows, use_container_width=True, hide_index=True)

    render_observations_table(filtered_observations)

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

    render_position_estimate(position_estimate, test_input_observations)
    render_architecture_note()


def render_top_networks(filtered_summary: pd.DataFrame) -> None:
    st.subheader("Haeufig beobachtete Netzwerke")
    st.dataframe(
        filtered_summary[
            [
                "ssid",
                "bssid",
                "scan_count",
                "total_observations",
                "mean_rssi",
            ]
        ].head(15),
        use_container_width=True,
        hide_index=True,
    )


def render_observations_table(filtered_observations: pd.DataFrame) -> None:
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
        ].head(300),
        use_container_width=True,
        hide_index=True,
    )

    if len(filtered_observations) > 300:
        st.caption("Es werden nur die ersten 300 Beobachtungen angezeigt.")


def render_position_estimate(position_estimate: object | None, test_input_observations: pd.DataFrame) -> None:
    st.subheader("Standort-Testrun")

    if test_input_observations.empty:
        st.info("Aktiviere links den Standort-Test, um aus WLAN-Werten eine Position zu schaetzen.")
        return

    st.write(f"Eingegebene WLAN-Netzwerke: {len(test_input_observations)}")

    if position_estimate is None:
        st.warning(
            "Keine Position gefunden. Mindestens eine eingegebene `SSID+BSSID`-Kombination "
            "muss in der Referenzdatenbank vorkommen."
        )
        return

    st.success("Geschaetzter Standort wurde auf der Karte markiert.")
    st.write(f"Latitude: `{position_estimate['latitude']:.6f}`")
    st.write(f"Longitude: `{position_estimate['longitude']:.6f}`")
    st.write(f"Beste RSSI-Abweichung: {position_estimate['best_rmse']:.1f}")
    st.write(f"Gemeinsame Netzwerke: {position_estimate['matched_networks']}")

    if position_estimate["error_m"] is not None:
        st.write(f"Fehler gegen echten Test-Scan: {position_estimate['error_m']:.1f} m")

    st.dataframe(
        position_estimate["candidates"][
            ["scan_id", "rmse", "matched_networks", "latitude", "longitude"]
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_architecture_note() -> None:
    st.subheader("Architekturhinweis")
    st.write(
        "Die Software modelliert pro Messung nur einen moeglichen Radius. "
        "Ein exakter Routerstandort wird nicht behauptet. Erst mehrere Beobachtungen "
        "desselben Netzwerks koennen einen wahrscheinlicheren Bereich ergeben."
    )


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.fingerprint_localization import (
    get_scan_input_observations,
    parse_manual_wifi_input,
    run_leave_one_scan_out_benchmark,
)
from src.load_wifi_csv import load_wifi_csv
from src.evaluation import (
    DEFAULT_DISPLAY_RADIUS_M,
    ROUTE_COMPARISON_COLUMNS,
    build_route_comparison,
    filter_points_by_radius,
    summarize_route_accuracy,
)
from src.localization_logic import (
    estimate_overlap_points,
    estimate_position_from_access_points,
)
from src.preprocess_wifi_data import clean_wifi_data, create_scan_summary
from src.project_pipeline import load_runtime_data
from src.visualize_wifi_data import build_router_map, load_osm_map

RAW_CSV_PATH = Path("data/raw/WigleWifi_20260408161721.csv")
RAW_OSM_PATH = Path("data/raw/map_innenstadt.osm")
PROCESSED_DIR = Path("data/processed")
ALL_OPTION = "Alle"
MAX_RADIUS_OBSERVATIONS = 1000
OVERLAP_COLUMNS = ["latitude", "longitude", "support_count", "network_id", "ssid", "bssid", "color"]


@st.cache_data(show_spinner=False)
def load_runtime_bundle() -> dict[str, object]:
    return load_runtime_data(PROCESSED_DIR)


@st.cache_data(show_spinner=False)
def load_osm_data() -> dict[str, object]:
    return load_osm_map(RAW_OSM_PATH)


@st.cache_data(show_spinner=False)
def load_calibration_bundle() -> dict[str, object] | None:
    if not RAW_CSV_PATH.exists():
        return None

    raw_dataframe = load_wifi_csv(RAW_CSV_PATH)
    cleaned_dataframe = clean_wifi_data(
        raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    scan_summary = create_scan_summary(cleaned_dataframe)
    return {
        "cleaned_dataframe": cleaned_dataframe,
        "scan_summary": scan_summary,
    }


@st.cache_data(show_spinner=False)
def load_route_comparison_data() -> pd.DataFrame:
    calibration_bundle = load_calibration_bundle()
    if calibration_bundle is None:
        return pd.DataFrame(columns=ROUTE_COMPARISON_COLUMNS)

    runtime_data = load_runtime_bundle()
    return build_route_comparison(
        calibration_bundle["scan_summary"],
        runtime_data["scan_summary"],
    )


def main() -> None:
    st.set_page_config(page_title="WiFi Selbstlokalisierung", layout="wide")
    st.title("WiFi-basierte Selbstlokalisierung")
    st.write(
        "Die Laufzeitansicht arbeitet mit triangulierten Access Points und "
        "triangulierten Scan-Punkten. Roh-GPS wird im normalen Endtest nicht verwendet."
    )

    if not RAW_OSM_PATH.exists():
        st.error(f"OSM-Datei fehlt: {RAW_OSM_PATH}")
        return

    try:
        runtime_data = load_runtime_bundle()
    except FileNotFoundError as error:
        st.error("Verarbeitete Artefakte fehlen. Starte zuerst `py main.py`, um die Triangulationsdaten zu erzeugen.")
        st.caption(str(error))
        return

    with st.spinner("Daten werden geladen..."):
        osm_map = load_osm_data()

    scan_summary = runtime_data["scan_summary"]
    network_summary = runtime_data["network_summary"]
    network_observations = runtime_data["network_observations"]
    dataset_summary = runtime_data["dataset_summary"]
    access_points = runtime_data["access_points"]

    selected_ssid, selected_bssid = render_filters(network_summary)
    position_estimate, test_input_observations, show_route_comparison = render_position_test_controls(access_points)
    filtered_summary = filter_network_summary(network_summary, selected_ssid, selected_bssid)
    filtered_observations = filter_network_observations(network_observations, selected_ssid, selected_bssid)
    map_observations = get_map_observations(filtered_observations, selected_ssid, selected_bssid)
    network_colors = build_network_colors(filtered_summary["network_id"].tolist())
    if should_calculate_overlap(filtered_summary, selected_ssid, selected_bssid):
        overlap_points = build_overlap_points(filtered_summary, map_observations, network_colors)
    else:
        overlap_points = pd.DataFrame(columns=OVERLAP_COLUMNS)

    if show_route_comparison:
        with st.spinner("GPS-Route und WLAN-Schaetzroute werden verglichen..."):
            route_comparison = load_route_comparison_data()
    else:
        route_comparison = pd.DataFrame(columns=ROUTE_COMPARISON_COLUMNS)

    focus_latitude, focus_longitude = get_position_focus(position_estimate)
    focused_observations = filter_points_by_radius(
        focus_latitude,
        focus_longitude,
        map_observations,
        radius_m=DEFAULT_DISPLAY_RADIUS_M,
    )
    focused_access_points = get_display_access_points(
        access_points,
        filtered_summary,
        selected_ssid,
        selected_bssid,
        focus_latitude,
        focus_longitude,
    )

    with st.spinner("Standort-Karte wird aufgebaut..."):
        estimate_map = build_router_map(
            osm_map,
            scan_summary,
            focused_observations,
            overlap_points,
            network_colors,
            focused_access_points,
            position_estimate,
        )

    left_column, right_column = st.columns([2.4, 1])

    with left_column:
        estimate_tab, comparison_tab = st.tabs(["Standort-Schaetzung", "GPS-vs-WLAN-Vergleich"])

        with estimate_tab:
            st.subheader("Standort-Schaetzung")
            st.caption(
                f"Radius- und AP-Layer werden um die aktuelle Schaetzung auf {DEFAULT_DISPLAY_RADIUS_M:.0f} m begrenzt."
            )
            st_folium(estimate_map, use_container_width=True, height=780)

        with comparison_tab:
            st.subheader("GPS-vs-WLAN-Vergleich")
            if route_comparison.empty:
                st.info("Aktiviere links `GPS-Route mit WLAN-Schaetzung vergleichen`, um den Vergleich zu sehen.")
            else:
                with st.spinner("Vergleichs-Karte wird aufgebaut..."):
                    comparison_map = build_router_map(
                        osm_map,
                        scan_summary,
                        pd.DataFrame(columns=map_observations.columns),
                        pd.DataFrame(columns=OVERLAP_COLUMNS),
                        network_colors,
                        pd.DataFrame(columns=access_points.columns),
                        route_comparison=route_comparison,
                        show_scan_markers=False,
                        show_access_points=False,
                    )
                st_folium(comparison_map, use_container_width=True, height=780)

    with right_column:
        render_sidebar_content(
            dataset_summary,
            filtered_summary,
            filtered_observations,
            focused_observations,
            overlap_points,
            network_colors,
            selected_ssid,
            selected_bssid,
            position_estimate,
            test_input_observations,
            focused_access_points,
            route_comparison,
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
    access_points: pd.DataFrame,
) -> tuple[object | None, pd.DataFrame, bool]:
    empty_observations = pd.DataFrame(columns=["network_id", "ssid", "bssid", "rssi"])

    with st.sidebar:
        st.header("Standort-Test")
        mode = st.selectbox(
            "Modus",
            ["Aus", "Manuelle Eingabe", "Dev-Benchmark"],
            index=0,
        )
        min_matches = st.slider("Minimale AP-Treffer", min_value=3, max_value=6, value=3)
        show_route_comparison = st.checkbox("GPS-Route mit WLAN-Schaetzung vergleichen", value=False)

        if mode == "Aus":
            return None, empty_observations, show_route_comparison

        if mode == "Manuelle Eingabe":
            manual_text = st.text_area(
                "WLAN-Werte",
                placeholder="SSID,BSSID,RSSI\neduroam,aa:bb:cc:dd:ee:ff,-65",
                height=140,
            )
            input_observations = parse_manual_wifi_input(manual_text)
            estimate = estimate_position_from_access_points(
                access_points,
                input_observations,
                min_matches=min_matches,
            )
            return estimate, input_observations, show_route_comparison

        calibration_bundle = load_calibration_bundle()
        if calibration_bundle is None:
            st.warning("Kein Rohdatensatz mit GPS verfuegbar. Der Dev-Benchmark ist daher deaktiviert.")
            return None, empty_observations, show_route_comparison

        scan_ids = calibration_bundle["scan_summary"]["scan_id"].tolist()
        selected_scan_id = st.selectbox("Benchmark-Scan", scan_ids, index=0)
        input_observations = get_scan_input_observations(
            calibration_bundle["cleaned_dataframe"],
            selected_scan_id,
        )
        estimate = run_leave_one_scan_out_benchmark(
            calibration_bundle["cleaned_dataframe"],
            selected_scan_id,
            min_matches=min_matches,
        )
        return estimate, input_observations, show_route_comparison


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


def get_position_focus(position_estimate: object | None) -> tuple[float | None, float | None]:
    if position_estimate is None:
        return None, None

    return float(position_estimate["latitude"]), float(position_estimate["longitude"])


def get_display_access_points(
    access_points: pd.DataFrame,
    filtered_summary: pd.DataFrame,
    selected_ssid: str,
    selected_bssid: str,
    focus_latitude: float | None,
    focus_longitude: float | None,
) -> pd.DataFrame:
    if access_points.empty:
        return access_points.copy()

    if focus_latitude is not None and focus_longitude is not None:
        return filter_points_by_radius(
            focus_latitude,
            focus_longitude,
            access_points,
            radius_m=DEFAULT_DISPLAY_RADIUS_M,
        )

    if selected_ssid == ALL_OPTION and selected_bssid == ALL_OPTION:
        return access_points.iloc[0:0].copy()

    network_ids = set(filtered_summary["network_id"].dropna().tolist())
    return access_points.loc[access_points["network_id"].isin(network_ids)].reset_index(drop=True)


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
    access_points: pd.DataFrame,
    route_comparison: pd.DataFrame,
) -> None:
    st.subheader("Datensatz")
    st.metric("Scans", int(dataset_summary["scans"]))
    st.metric("Gefilterte Netzwerke", int(filtered_summary["network_id"].nunique()))
    st.metric("APs auf Karte", int(len(access_points)))

    st.subheader("Gefilterte Auswahl")
    if filtered_summary.empty:
        st.warning("Mit dieser Filterkombination wurden keine Netzwerke gefunden.")
        return

    if selected_ssid == ALL_OPTION and selected_bssid == ALL_OPTION:
        st.info(
            "Uebersicht: Es werden triangulierte Scan-Punkte und Access Points angezeigt. "
            "Waehle eine SSID oder MAC-Adresse aus, um Schaetzkreise einzublenden."
        )
        render_top_networks(filtered_summary)
        render_position_estimate(position_estimate, test_input_observations)
        render_route_comparison_summary(route_comparison)
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
        st.write(f"Ueberlappungspunkte: {len(overlap_points)}")
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
            "aus mindestens zwei triangulierten Scan-Beobachtungen desselben Netzwerks."
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
    render_route_comparison_summary(route_comparison)
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
            "Keine Position gefunden. Es muessen mindestens drei eingegebene `SSID+BSSID`-Kombinationen "
            "als triangulierte Access Points bekannt sein."
        )
        return

    st.success("Geschaetzter Standort wurde auf der Karte markiert.")
    st.write(f"Latitude: `{position_estimate['latitude']:.6f}`")
    st.write(f"Longitude: `{position_estimate['longitude']:.6f}`")
    st.write(f"Residual-RMSE: {position_estimate['residual_rmse']:.1f} m")
    st.write(f"Gematchte APs: {position_estimate['matched_networks']}")
    st.write(f"Konfidenz: {position_estimate['confidence_score']:.2f}")

    if position_estimate["error_m"] is not None:
        st.write(f"Benchmark-Fehler gegen GPS-Referenz: {position_estimate['error_m']:.1f} m")

    matched_access_points = position_estimate.get("matched_access_points")
    if isinstance(matched_access_points, pd.DataFrame) and not matched_access_points.empty:
        st.dataframe(
            matched_access_points[
                ["ssid", "bssid", "rssi", "estimated_radius_m", "quality_flag"]
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_route_comparison_summary(route_comparison: pd.DataFrame) -> None:
    st.subheader("Routenvergleich")

    if route_comparison.empty:
        st.info("Aktiviere links `GPS-Route mit WLAN-Schaetzung vergleichen`, um GPS und WLAN-Schaetzung zu vergleichen.")
        return

    summary = summarize_route_accuracy(route_comparison)
    st.success("GPS-Route, WLAN-Schaetzpunkte und Verbindungslinien sind auf der Karte aktiv.")
    st.write(f"Verglichene Scans: {summary['compared_scans']}")
    st.write(f"Mittlerer Fehler: {summary['mean_error_m']:.1f} m")
    st.write(f"Medianfehler: {summary['median_error_m']:.1f} m")
    st.write(f"Maximaler Fehler: {summary['max_error_m']:.1f} m")
    st.dataframe(
        route_comparison[
            [
                "scan_id",
                "matched_access_points",
                "residual_rmse",
                "error_m",
            ]
        ].head(80),
        use_container_width=True,
        hide_index=True,
    )


def render_architecture_note() -> None:
    st.subheader("Architekturhinweis")
    st.write(
        "Die Runtime nutzt nur triangulierte Access Points und RSSI-basierte Distanzschaetzungen. "
        "Roh-GPS ist nur fuer die Offline-Kalibrierung und den optionalen Dev-Benchmark relevant."
    )


if __name__ == "__main__":
    main()

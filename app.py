from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.load_wifi_csv import load_wifi_csv
from src.localization_logic import (
    create_network_observations,
    estimate_overlap_points,
    estimate_position_from_access_points,
    estimate_router_position_from_observations,
)
from src.preprocess_wifi_data import clean_wifi_data
from src.project_pipeline import load_runtime_data
from src.road_constraints import snap_position_to_nearest_road
from src.route_estimation import summarize_wifi_route
from src.visualize_wifi_data import (
    build_route_estimation_map,
    build_router_estimation_map,
    build_simple_location_map,
    load_osm_map,
)
from src.wifi_input_matching import match_wifi_measurements

RAW_CSV_PATH = Path("data/raw/WigleWifi_20260408161721.csv")
RAW_OSM_PATH = Path("data/raw/map_innenstadt.osm")
PROCESSED_DIR = Path("data/processed")
DEFAULT_MIN_MATCHES = 3
MAX_ROUTER_OBSERVATIONS_ON_MAP = 250
SSID_COLORS = [
    "#2563eb",
    "#dc2626",
    "#16a34a",
    "#f97316",
    "#7c3aed",
    "#0891b2",
    "#be123c",
    "#4d7c0f",
]


@st.cache_data(show_spinner=False)
def load_runtime_bundle() -> dict[str, object]:
    return load_runtime_data(PROCESSED_DIR)


@st.cache_data(show_spinner=False)
def load_osm_data() -> dict[str, object]:
    return load_osm_map(RAW_OSM_PATH)


@st.cache_data(show_spinner=False)
def load_router_calibration_bundle() -> dict[str, pd.DataFrame]:
    raw_dataframe = load_wifi_csv(RAW_CSV_PATH)
    calibration_dataframe = clean_wifi_data(
        raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )
    network_observations = create_network_observations(calibration_dataframe)
    return {
        "calibration_dataframe": calibration_dataframe,
        "network_observations": network_observations,
    }


def main() -> None:
    st.set_page_config(page_title="WiFi Standorttest", layout="wide")
    st.title("WiFi-Standorttest")
    st.write(
        "Gib mehrere WLAN-Messwerte ein. Die App schaetzt daraus den Standort "
        "und setzt ihn auf die naechste begehbare Strasse oder einen Fussweg."
    )

    if not RAW_OSM_PATH.exists():
        st.error(f"OSM-Datei fehlt: {RAW_OSM_PATH}")
        return

    try:
        runtime_data = load_runtime_bundle()
    except FileNotFoundError as error:
        st.error("Verarbeitete Artefakte fehlen. Starte zuerst `py main.py`.")
        st.caption(str(error))
        return

    osm_map = load_osm_data()
    access_points = runtime_data["access_points"]

    location_tab, router_tab, route_tab = st.tabs(["Standort-Test", "Router-Schaetzung", "Laufweg-Vergleich"])

    with location_tab:
        wifi_text, min_matches, should_estimate = render_location_inputs(access_points)
        render_location_tab(wifi_text, min_matches, should_estimate, access_points, osm_map)

    with router_tab:
        render_router_estimation_tab(osm_map)

    with route_tab:
        render_route_comparison_tab(runtime_data.get("route_comparison", pd.DataFrame()), osm_map)


def render_location_tab(
    wifi_text: str,
    min_matches: int,
    should_estimate: bool,
    access_points: pd.DataFrame,
    osm_map: dict[str, object],
) -> None:
    result = None
    matched_measurements = pd.DataFrame()
    ignored_measurements = pd.DataFrame()

    if should_estimate:
        result, matched_measurements, ignored_measurements = estimate_location_on_road(
            wifi_text,
            access_points,
            osm_map,
            min_matches=min_matches,
        )

    location_map = build_simple_location_map(osm_map, result)
    left_column, right_column = st.columns([2.3, 1])

    with left_column:
        st.subheader("Geschaetzter Standort")
        st_folium(location_map, use_container_width=True, height=720, key="location_map")

    with right_column:
        render_result_panel(result, matched_measurements, ignored_measurements)


def render_router_estimation_tab(osm_map: dict[str, object]) -> None:
    st.subheader("Router-Schaetzung aus RSSI-Kreisen")
    st.write(
        "Hier wird pro Messpunkt ein Kreis aus dem RSSI-Wert gebildet. "
        "Ab 3 Messpunkten wird der beste gemeinsame Kreispunkt gesucht; bei weniger Messpunkten "
        "nutzt die App eine einfache Schnittpunkt-/Feder-Schaetzung."
    )

    if not RAW_CSV_PATH.exists():
        st.error(f"Rohdaten fuer Router-Schaetzung fehlen: {RAW_CSV_PATH}")
        return

    router_data = load_router_calibration_bundle()
    observations = router_data["network_observations"]
    selected_observations, selected_ssid, selected_bssid = render_router_filters(observations)

    if selected_observations.empty:
        st.info("Waehle eine SSID oder eine konkrete BSSID aus, um Messpunkte und RSSI-Kreise zu sehen.")
        render_router_dataset_overview(observations)
        empty_map = build_router_estimation_map(osm_map, pd.DataFrame(), pd.DataFrame(), {}, pd.DataFrame())
        st_folium(empty_map, use_container_width=True, height=700, key="router_empty_map")
        return

    if len(selected_observations) > MAX_ROUTER_OBSERVATIONS_ON_MAP:
        st.warning(
            f"Die Auswahl enthaelt {len(selected_observations)} Beobachtungen. "
            "Bitte eine konkrete BSSID waehlen, damit die Karte fluessig bleibt."
        )
        render_router_dataset_overview(selected_observations)
        return

    ssid_colors = build_ssid_color_map(selected_observations["ssid"].dropna().unique())
    router_estimates = build_router_estimates(selected_observations)
    overlap_points = build_router_overlap_points(selected_observations, ssid_colors)
    router_map = build_router_estimation_map(
        osm_map,
        selected_observations,
        router_estimates,
        ssid_colors,
        overlap_points,
    )

    left_column, right_column = st.columns([2.3, 1])
    with left_column:
        st_folium(router_map, use_container_width=True, height=720, key="router_estimation_map")
    with right_column:
        render_router_result_panel(
            selected_observations,
            router_estimates,
            overlap_points,
            selected_ssid,
            selected_bssid,
        )


def render_route_comparison_tab(route_estimates: pd.DataFrame, osm_map: dict[str, object]) -> None:
    st.subheader("GPS-Laufweg vs. WLAN-Laufweg")
    st.write(
        "Die rote Linie ist der echte GPS-Laufweg. Die blaue Linie ist der nur aus WLAN-Signalen "
        "geschaetzte Laufweg. Orange Linien zeigen die Abweichung zwischen GPS-Punkt und WLAN-Schaetzung."
    )

    if route_estimates.empty:
        st.warning("Laufweg-Vergleich fehlt. Starte zuerst `py main.py`, damit route_comparison.csv erzeugt wird.")
        return

    min_matches = st.slider(
        "Minimale AP-Treffer fuer WLAN-Laufweg",
        min_value=1,
        max_value=6,
        value=2,
        key="route_min_matches",
    )
    route_estimates = route_estimates.loc[route_estimates["matched_access_points"] >= min_matches].copy()
    route_map = build_route_estimation_map(osm_map, route_estimates)

    left_column, right_column = st.columns([2.3, 1])
    with left_column:
        st_folium(route_map, use_container_width=True, height=720, key="route_comparison_map")
    with right_column:
        render_route_result_panel(route_estimates)


def render_location_inputs(access_points: pd.DataFrame) -> tuple[str, int, bool]:
    st.subheader("WLAN-Werte eingeben")
    st.caption("Format pro Zeile: `SSID,BSSID,RSSI`")
    wifi_text = st.text_area(
        "WLAN-Werte",
        value=build_example_input(access_points),
        height=190,
        key="location_wifi_input",
    )
    min_matches = st.slider(
        "Minimale AP-Treffer",
        min_value=2,
        max_value=6,
        value=DEFAULT_MIN_MATCHES,
        key="location_min_matches",
    )
    should_estimate = st.button("Standort schaetzen", type="primary")

    return wifi_text, min_matches, should_estimate


def render_router_filters(observations: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    filter_column, _ = st.columns([1, 2])
    with filter_column:
        ssid_options = ["Alle"] + sorted(observations["ssid"].dropna().astype(str).unique().tolist())
        selected_ssid = st.selectbox("SSID", ssid_options, key="router_ssid")

        bssid_source = observations
        if selected_ssid != "Alle":
            bssid_source = bssid_source.loc[bssid_source["ssid"] == selected_ssid]
        bssid_options = ["Alle"] + sorted(bssid_source["bssid"].dropna().astype(str).unique().tolist())
        selected_bssid = st.selectbox("BSSID / Router", bssid_options, key="router_bssid")

    if selected_ssid == "Alle" and selected_bssid == "Alle":
        return pd.DataFrame(), selected_ssid, selected_bssid

    selected = observations.copy()
    if selected_ssid != "Alle":
        selected = selected.loc[selected["ssid"] == selected_ssid].copy()
    if selected_bssid != "Alle":
        selected = selected.loc[selected["bssid"] == selected_bssid].copy()
    return selected, selected_ssid, selected_bssid


def build_ssid_color_map(ssids: list[str] | pd.Index) -> dict[str, str]:
    return {
        str(ssid): SSID_COLORS[index % len(SSID_COLORS)]
        for index, ssid in enumerate(sorted(str(ssid) for ssid in ssids))
    }


def build_router_estimates(observations: pd.DataFrame) -> pd.DataFrame:
    estimates: list[dict[str, object]] = []
    if observations.empty:
        return pd.DataFrame(columns=router_estimate_columns())

    for _, network_rows in observations.groupby(["network_id", "ssid", "bssid"]):
        estimate = estimate_router_position_from_observations(network_rows)
        if estimate is not None:
            estimates.append(estimate)

    if not estimates:
        return pd.DataFrame(columns=router_estimate_columns())

    return pd.DataFrame(estimates, columns=router_estimate_columns()).sort_values(
        ["quality_flag", "scan_count", "rmse_m"],
        ascending=[True, False, True],
    )


def build_router_overlap_points(
    observations: pd.DataFrame,
    ssid_colors: dict[str, str],
) -> pd.DataFrame:
    if observations.empty or observations["network_id"].nunique() != 1:
        return pd.DataFrame(columns=["latitude", "longitude", "support_count", "ssid", "bssid", "color"])

    overlap_points = estimate_overlap_points(observations, step_m=2.5, min_support=3)
    if overlap_points.empty:
        return overlap_points

    first_row = observations.iloc[0]
    overlap_points = overlap_points.copy()
    overlap_points["ssid"] = first_row["ssid"]
    overlap_points["bssid"] = first_row["bssid"]
    overlap_points["color"] = ssid_colors.get(first_row["ssid"], "#dc2626")
    return overlap_points


def router_estimate_columns() -> list[str]:
    return [
        "network_id",
        "ssid",
        "bssid",
        "latitude",
        "longitude",
        "scan_count",
        "total_observations",
        "mean_rssi",
        "min_radius_m",
        "max_radius_m",
        "rmse_m",
        "quality_flag",
        "method",
    ]


def render_router_dataset_overview(observations: pd.DataFrame) -> None:
    st.metric("Beobachtungen", len(observations))
    st.metric("SSIDs", observations["ssid"].nunique())
    st.metric("SSID+BSSID", observations["network_id"].nunique())


def render_router_result_panel(
    selected_observations: pd.DataFrame,
    router_estimates: pd.DataFrame,
    overlap_points: pd.DataFrame,
    selected_ssid: str,
    selected_bssid: str,
) -> None:
    st.subheader("Auswahl")
    st.write(f"SSID: `{selected_ssid}`")
    st.write(f"BSSID: `{selected_bssid}`")
    st.metric("Messkreise", len(selected_observations))
    st.metric("Geschaetzte Router", len(router_estimates))

    if router_estimates.empty:
        st.warning("Fuer diese Auswahl gibt es noch keinen Routerstandort.")
    else:
        best_router = router_estimates.iloc[0]
        st.success("Routerstandort wurde aus den Messkreisen geschaetzt.")
        st.write(f"Koordinate: `{best_router['latitude']:.6f}, {best_router['longitude']:.6f}`")
        st.write(f"RMSE: `{best_router['rmse_m']:.1f} m`")
        st.write(f"Qualitaet: `{best_router['quality_flag']}`")
        st.write(f"Methode: `{best_router['method']}`")
        st.dataframe(
            router_estimates[["ssid", "bssid", "scan_count", "rmse_m", "quality_flag", "method"]],
            use_container_width=True,
            hide_index=True,
        )

    if selected_observations["network_id"].nunique() == 1:
        st.metric("Schnittpunkte mit min. 3 Kreisen", len(overlap_points))
    else:
        st.info("Schnittpunkte werden nur fuer eine konkrete SSID+BSSID berechnet.")


def render_route_result_panel(route_estimates: pd.DataFrame) -> None:
    st.subheader("Laufweg-Auswertung")
    if route_estimates.empty:
        st.warning("Es konnten keine WLAN-Laufwegpunkte geschaetzt werden.")
        return

    summary = summarize_wifi_route(route_estimates)
    st.metric("Verglichene Scans", summary["estimated_scans"])
    st.metric("Mittlerer Fehler", f"{summary['mean_error_m']:.1f} m")
    st.metric("Median-Fehler", f"{summary['median_error_m']:.1f} m")
    st.metric("Max. Fehler", f"{summary['max_error_m']:.1f} m")

    st.write("Farben:")
    st.write("GPS-Laufweg: rot")
    st.write("WLAN-Laufweg: blau")
    st.write("Abweichung GPS zu WLAN: orange")

    with st.expander("Scan-Details"):
        st.dataframe(
            route_estimates[
                [
                    "scan_id",
                    "matched_access_points",
                    "residual_rmse",
                    "snap_distance_m",
                    "error_m",
                    "method",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


def build_example_input(access_points: pd.DataFrame, count: int = 3) -> str:
    if access_points.empty:
        return "SSID,BSSID,RSSI"

    rows = ["SSID,BSSID,RSSI"]
    for row in access_points.head(count).itertuples(index=False):
        rssi = int(round(getattr(row, "mean_rssi", -70)))
        rows.append(f"{row.ssid},{row.bssid},{rssi}")
    return "\n".join(rows)


def estimate_location_on_road(
    wifi_text: str,
    access_points: pd.DataFrame,
    osm_map: dict[str, object],
    *,
    min_matches: int = DEFAULT_MIN_MATCHES,
) -> tuple[dict[str, object] | None, pd.DataFrame, pd.DataFrame]:
    matched_measurements, ignored_measurements = match_wifi_measurements(wifi_text, access_points)
    if matched_measurements.empty:
        return None, matched_measurements, ignored_measurements

    raw_estimate = estimate_position_from_access_points(
        access_points,
        matched_measurements,
        min_matches=min_matches,
    )
    if raw_estimate is None:
        return None, matched_measurements, ignored_measurements

    snapped_position = snap_position_to_nearest_road(
        raw_estimate["latitude"],
        raw_estimate["longitude"],
        osm_map,
    )
    result = {
        **raw_estimate,
        "raw_latitude": raw_estimate["latitude"],
        "raw_longitude": raw_estimate["longitude"],
        "latitude": snapped_position["latitude"],
        "longitude": snapped_position["longitude"],
        "snap_distance_m": snapped_position["snap_distance_m"],
        "road_type": snapped_position["road_type"],
        "snapped": snapped_position["snapped"],
    }
    return result, matched_measurements, ignored_measurements


def render_result_panel(
    result: dict[str, object] | None,
    matched_measurements: pd.DataFrame,
    ignored_measurements: pd.DataFrame,
) -> None:
    st.subheader("Ergebnis")

    if result is None:
        st.info("Klicke links auf `Standort schaetzen`, um einen Standort zu berechnen.")
        if not ignored_measurements.empty:
            st.warning("Einige Eingabezeilen konnten nicht verwendet werden.")
            st.dataframe(ignored_measurements, use_container_width=True, hide_index=True)
        return

    st.success("Standort wurde geschaetzt und auf einen begehbaren Weg gesetzt.")
    st.metric("Gematchte Netzwerke", int(result["matched_networks"]))
    st.metric("RMSE", f"{result['residual_rmse']:.1f} m")
    snap_distance = result.get("snap_distance_m")
    if snap_distance is not None:
        st.metric("Distanz zur Strasse", f"{snap_distance:.1f} m")
    st.write(f"Koordinate: `{result['latitude']:.6f}, {result['longitude']:.6f}`")
    st.write(f"OSM-Wegtyp: `{result.get('road_type') or 'nicht gefunden'}`")

    with st.expander("Technische Details"):
        st.write("Roh-Schaetzung vor dem Strassen-Snapping:")
        st.write(f"`{result['raw_latitude']:.6f}, {result['raw_longitude']:.6f}`")

        if not matched_measurements.empty:
            st.write("Verwendete WLAN-Eingaben:")
            st.dataframe(
                matched_measurements[["ssid", "bssid", "rssi", "input_ssid", "input_bssid", "ssid_similarity"]],
                use_container_width=True,
                hide_index=True,
            )

        matched_access_points = result.get("matched_access_points")
        if isinstance(matched_access_points, pd.DataFrame) and not matched_access_points.empty:
            st.write("Gematchte triangulierte Access Points:")
            st.dataframe(
                matched_access_points[["ssid", "bssid", "rssi", "estimated_radius_m", "quality_flag"]],
                use_container_width=True,
                hide_index=True,
            )

        if not ignored_measurements.empty:
            st.write("Ignorierte Eingaben:")
            st.dataframe(ignored_measurements, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

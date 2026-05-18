from pathlib import Path

from src.load_wifi_csv import load_wifi_csv
from src.preprocess_wifi_data import clean_wifi_data
from src.project_pipeline import run_data_pipeline
from src.route_estimation import (
    add_route_quality_flags,
    build_gps_route_matched,
    build_gps_route_raw,
    build_route_comparison_with_matched_gps,
    build_wknn_route_comparison,
    save_route_estimates,
)
from src.visualize_wifi_data import load_osm_map

RAW_CSV_PATH = Path("data/raw/WigleWifi_20260408161721.csv")
RAW_OSM_PATH = Path("data/raw/map_innenstadt.osm")
PROCESSED_DIR = Path("data/processed")
CORE_PROCESSED_FILES = [
    "wifi_scans_clean.csv",
    "scan_summary.csv",
    "network_observations.csv",
    "network_summary.csv",
    "triangulated_access_points.csv",
    "triangulated_scan_positions.csv",
    "dataset_summary.txt",
]


def main() -> None:
    if not RAW_CSV_PATH.exists():
        print(f"Keine CSV-Datei gefunden: {RAW_CSV_PATH}")
        print("Lege die Datei in data/raw/ ab und starte das Skript erneut.")
        return

    osm_path = RAW_OSM_PATH if RAW_OSM_PATH.exists() else None
    if processed_baseline_exists():
        pipeline_data = update_fast_runtime_outputs(RAW_CSV_PATH, PROCESSED_DIR, osm_path)
    else:
        pipeline_data = run_data_pipeline(RAW_CSV_PATH, PROCESSED_DIR, osm_path)
    csv_info = pipeline_data["csv_info"]
    dataset_summary = pipeline_data["dataset_summary"]
    output_paths = pipeline_data["output_paths"]

    print("CSV-Ueberblick:")
    print(f"- Datei: {csv_info['file_name']}")
    print(f"- Wigle-Metazeile erkannt: {csv_info['skip_app_header']}")
    print(f"- Gesamtzeilen: {csv_info['total_lines']}")
    print(f"- Datenzeilen: {csv_info['data_rows']}")
    print("- Spalten:")
    for column_name in csv_info["columns"]:
        print(f"  - {column_name}")

    print("\nDatensatz-Zusammenfassung:")
    for key, value in dataset_summary.items():
        print(f"- {key}: {value}")

    print("\nGespeicherte Dateien:")
    for output_path in output_paths:
        print(f"- {output_path}")

    print("\nInteraktive Anwendung starten mit:")
    print("py -m streamlit run app.py")


def processed_baseline_exists() -> bool:
    return all((PROCESSED_DIR / file_name).exists() for file_name in CORE_PROCESSED_FILES)


def update_fast_runtime_outputs(
    raw_csv_path: Path,
    processed_dir: Path,
    osm_path: Path | None,
) -> dict[str, object]:
    from src.project_pipeline import load_runtime_data

    runtime_data = load_runtime_data(processed_dir)
    output_paths = [processed_dir / file_name for file_name in CORE_PROCESSED_FILES]

    wknn_paths = {
        "route_comparison_wknn": processed_dir / "route_comparison_wknn.csv",
        "route_comparison_wknn_clean": processed_dir / "route_comparison_wknn_clean.csv",
        "route_comparison_wknn_outliers": processed_dir / "route_comparison_wknn_outliers.csv",
        "gps_route_raw": processed_dir / "gps_route_raw.csv",
        "gps_route_matched": processed_dir / "gps_route_matched.csv",
        "route_comparison_wknn_matched": processed_dir / "route_comparison_wknn_matched.csv",
        "route_comparison_wknn_matched_clean": processed_dir / "route_comparison_wknn_matched_clean.csv",
        "route_comparison_wknn_matched_outliers": processed_dir / "route_comparison_wknn_matched_outliers.csv",
    }
    if osm_path is not None and not all(path.exists() for path in wknn_paths.values()):
        raw_dataframe = load_wifi_csv(raw_csv_path)
        calibration_dataframe = clean_wifi_data(
            raw_dataframe,
            require_coordinates=True,
            include_coordinates=True,
        )
        osm_map = load_osm_map(osm_path)
        gps_route_raw = build_gps_route_raw(calibration_dataframe)
        gps_route_matched = build_gps_route_matched(calibration_dataframe, osm_map)
        route = build_wknn_route_comparison(calibration_dataframe, osm_map, k=5, min_matches=3)
        quality = add_route_quality_flags(
            route,
            min_aps=3,
            max_rmse_m=45,
            max_error_m=100,
            max_jump_m=80,
        )
        clean = quality.loc[~quality["is_outlier"]].reset_index(drop=True)
        outliers = quality.loc[quality["is_outlier"]].reset_index(drop=True)
        save_route_estimates(route, wknn_paths["route_comparison_wknn"])
        save_route_estimates(clean, wknn_paths["route_comparison_wknn_clean"])
        save_route_estimates(outliers, wknn_paths["route_comparison_wknn_outliers"])
        route_matched = build_route_comparison_with_matched_gps(route, gps_route_matched, osm_map)
        matched_quality = add_route_quality_flags(
            route_matched,
            min_aps=3,
            max_rmse_m=45,
            max_error_m=100,
            max_jump_m=80,
        )
        matched_clean = matched_quality.loc[~matched_quality["is_outlier"]].reset_index(drop=True)
        matched_outliers = matched_quality.loc[matched_quality["is_outlier"]].reset_index(drop=True)
        save_route_estimates(gps_route_raw, wknn_paths["gps_route_raw"])
        save_route_estimates(gps_route_matched, wknn_paths["gps_route_matched"])
        save_route_estimates(route_matched, wknn_paths["route_comparison_wknn_matched"])
        save_route_estimates(matched_clean, wknn_paths["route_comparison_wknn_matched_clean"])
        save_route_estimates(matched_outliers, wknn_paths["route_comparison_wknn_matched_outliers"])

    output_paths.extend(path for path in wknn_paths.values() if path.exists())

    return {
        "csv_info": {
            "file_name": raw_csv_path.name,
            "skip_app_header": "bereits verarbeitet",
            "total_lines": "bereits verarbeitet",
            "data_rows": "bereits verarbeitet",
            "columns": runtime_data["cleaned_dataframe"].columns.tolist(),
        },
        "dataset_summary": runtime_data["dataset_summary"],
        "output_paths": output_paths,
    }


if __name__ == "__main__":
    main()

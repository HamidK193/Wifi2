import subprocess
import sys
from pathlib import Path

from src.load_wifi_csv import load_wifi_csv
from src.preprocess_wifi_data import clean_wifi_data
from src.project_pipeline import build_route_outputs, load_runtime_data, run_data_pipeline, save_route_outputs

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


def main() -> int:
    if not RAW_CSV_PATH.exists():
        print(f"Keine CSV-Datei gefunden: {RAW_CSV_PATH}")
        print("Lege die Datei in data/raw/ ab und starte das Skript erneut.")
        return 1

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
    return run_project_tests()


def processed_baseline_exists() -> bool:
    return all((PROCESSED_DIR / file_name).exists() for file_name in CORE_PROCESSED_FILES)


def run_project_tests() -> int:
    sys.stdout.flush()
    print("\nAutomatische Tests starten:")
    print(f"{sys.executable} -m pytest")
    sys.stdout.flush()
    completed = subprocess.run([sys.executable, "-m", "pytest"], check=False)
    if completed.returncode == 0:
        print("\nTests erfolgreich abgeschlossen.")
    else:
        print(f"\nTests fehlgeschlagen mit Exitcode {completed.returncode}.")
    return completed.returncode


def update_fast_runtime_outputs(
    raw_csv_path: Path,
    processed_dir: Path,
    osm_path: Path | None,
) -> dict[str, object]:
    runtime_data = load_runtime_data(processed_dir)
    output_paths = [processed_dir / file_name for file_name in CORE_PROCESSED_FILES]
    if osm_path is not None:
        raw_dataframe = load_wifi_csv(raw_csv_path)
        calibration_dataframe = clean_wifi_data(
            raw_dataframe,
            require_coordinates=True,
            include_coordinates=True,
        )
        route_outputs = build_route_outputs(
            calibration_dataframe,
            runtime_data["scan_positions"],
            runtime_data["network_observations"],
            runtime_data["access_points"],
            osm_path,
        )
        output_paths.extend(save_route_outputs(route_outputs, processed_dir))

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
    raise SystemExit(main())

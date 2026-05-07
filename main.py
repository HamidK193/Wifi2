from pathlib import Path

from src.project_pipeline import run_data_pipeline

RAW_CSV_PATH = Path("data/raw/WigleWifi_20260408161721.csv")
RAW_OSM_PATH = Path("data/raw/map_innenstadt.osm")
PROCESSED_DIR = Path("data/processed")


def main() -> None:
    if not RAW_CSV_PATH.exists():
        print(f"Keine CSV-Datei gefunden: {RAW_CSV_PATH}")
        print("Lege die Datei in data/raw/ ab und starte das Skript erneut.")
        return

    osm_path = RAW_OSM_PATH if RAW_OSM_PATH.exists() else None
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


if __name__ == "__main__":
    main()

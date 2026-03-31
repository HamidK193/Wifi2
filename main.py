from pathlib import Path

from src.load_wifi_csv import inspect_wifi_csv, load_wifi_csv, print_csv_overview
from src.preprocess_wifi_data import (
    clean_wifi_data,
    create_scan_summary,
    save_cleaned_data,
    save_dataset_summary,
    save_scan_summary,
    summarize_dataset,
)
from src.visualize_wifi_data import create_osm_visualizations, create_visualizations

RAW_CSV_PATH = Path("data/raw/T1_zu_W1.csv")
RAW_OSM_PATH = Path("data/raw/map.osm")
PROCESSED_DIR = Path("data/processed")


def main() -> None:
    if not RAW_CSV_PATH.exists():
        print(f"Keine CSV-Datei gefunden: {RAW_CSV_PATH}")
        print("Lege die Datei in data/raw/ ab und starte das Skript erneut.")
        return

    csv_info = inspect_wifi_csv(RAW_CSV_PATH)
    print_csv_overview(csv_info)

    raw_dataframe = load_wifi_csv(RAW_CSV_PATH)
    cleaned_dataframe = clean_wifi_data(raw_dataframe)
    scan_summary = create_scan_summary(cleaned_dataframe)
    dataset_summary = summarize_dataset(cleaned_dataframe, scan_summary)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    clean_path = save_cleaned_data(
        cleaned_dataframe,
        PROCESSED_DIR / "wifi_scans_clean.csv",
    )
    scan_path = save_scan_summary(
        scan_summary,
        PROCESSED_DIR / "scan_summary.csv",
    )
    summary_path = save_dataset_summary(
        dataset_summary,
        PROCESSED_DIR / "dataset_summary.txt",
    )
    plot_paths = create_visualizations(cleaned_dataframe, scan_summary, PROCESSED_DIR)
    osm_plot_paths = []

    if RAW_OSM_PATH.exists():
        osm_plot_paths = create_osm_visualizations(scan_summary, RAW_OSM_PATH, PROCESSED_DIR)
    else:
        print(f"\nKeine OSM-Datei gefunden: {RAW_OSM_PATH}")
        print("Die OSM-Ueberlagerung wird uebersprungen.")

    print("\nDatensatz-Zusammenfassung:")
    for key, value in dataset_summary.items():
        print(f"- {key}: {value}")

    print("\nGespeicherte Dateien:")
    print(f"- {clean_path}")
    print(f"- {scan_path}")
    print(f"- {summary_path}")
    for plot_path in plot_paths:
        print(f"- {plot_path}")
    for plot_path in osm_plot_paths:
        print(f"- {plot_path}")


if __name__ == "__main__":
    main()

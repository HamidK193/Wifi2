from pathlib import Path

from src.load_wifi_csv import inspect_wifi_csv, load_wifi_csv
from src.localization_logic import (
    create_network_observations,
    create_network_summary,
    save_network_observations,
    save_network_summary,
)
from src.preprocess_wifi_data import (
    clean_wifi_data,
    create_scan_summary,
    save_cleaned_data,
    save_dataset_summary,
    save_scan_summary,
    summarize_dataset,
)


def run_data_pipeline(raw_csv_path: str | Path, processed_dir: str | Path) -> dict[str, object]:
    raw_path = Path(raw_csv_path)
    output_dir = Path(processed_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_info = inspect_wifi_csv(raw_path)
    raw_dataframe = load_wifi_csv(raw_path)
    cleaned_dataframe = clean_wifi_data(raw_dataframe)
    scan_summary = create_scan_summary(cleaned_dataframe)
    network_observations = create_network_observations(cleaned_dataframe)
    network_summary = create_network_summary(network_observations)
    dataset_summary = summarize_dataset(cleaned_dataframe, scan_summary)

    clean_path = save_cleaned_data(cleaned_dataframe, output_dir / "wifi_scans_clean.csv")
    scan_path = save_scan_summary(scan_summary, output_dir / "scan_summary.csv")
    network_observation_path = save_network_observations(
        network_observations,
        output_dir / "network_observations.csv",
    )
    network_summary_path = save_network_summary(
        network_summary,
        output_dir / "network_summary.csv",
    )
    summary_path = save_dataset_summary(dataset_summary, output_dir / "dataset_summary.txt")

    return {
        "csv_info": csv_info,
        "cleaned_dataframe": cleaned_dataframe,
        "scan_summary": scan_summary,
        "network_observations": network_observations,
        "network_summary": network_summary,
        "dataset_summary": dataset_summary,
        "output_paths": [
            clean_path,
            scan_path,
            network_observation_path,
            network_summary_path,
            summary_path,
        ],
    }

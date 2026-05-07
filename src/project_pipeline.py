from pathlib import Path

import pandas as pd

from src.load_wifi_csv import inspect_wifi_csv, load_wifi_csv
from src.localization_logic import (
    create_network_observations,
    create_network_summary,
    save_network_observations,
    save_network_summary,
    save_triangulated_access_points,
    save_triangulated_scan_positions,
    triangulate_access_points,
    triangulate_scan_positions,
)
from src.preprocess_wifi_data import (
    clean_wifi_data,
    create_scan_summary,
    save_cleaned_data,
    save_dataset_summary,
    save_scan_summary,
    summarize_dataset,
)
from src.route_estimation import ROUTE_ESTIMATE_COLUMNS, build_wifi_route_from_scan_positions, save_route_estimates
from src.visualize_wifi_data import load_osm_map

RUNTIME_FILE_NAMES = {
    "cleaned_dataframe": "wifi_scans_clean.csv",
    "scan_summary": "scan_summary.csv",
    "network_observations": "network_observations.csv",
    "network_summary": "network_summary.csv",
    "access_points": "triangulated_access_points.csv",
    "scan_positions": "triangulated_scan_positions.csv",
    "route_comparison": "route_comparison.csv",
    "dataset_summary": "dataset_summary.txt",
}


def run_data_pipeline(
    raw_csv_path: str | Path,
    processed_dir: str | Path,
    osm_path: str | Path | None = None,
) -> dict[str, object]:
    raw_path = Path(raw_csv_path)
    output_dir = Path(processed_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_info = inspect_wifi_csv(raw_path)
    raw_dataframe = load_wifi_csv(raw_path)

    runtime_dataframe = clean_wifi_data(
        raw_dataframe,
        require_coordinates=False,
        include_coordinates=False,
    )
    calibration_dataframe = clean_wifi_data(
        raw_dataframe,
        require_coordinates=True,
        include_coordinates=True,
    )

    access_points = triangulate_access_points(calibration_dataframe)
    scan_positions = triangulate_scan_positions(runtime_dataframe, access_points)
    if scan_positions.empty:
        raise ValueError("Es konnten keine GPS-freien Scan-Positionen aus den triangulierten Access Points geschaetzt werden.")

    scan_summary = create_scan_summary(runtime_dataframe, scan_positions)
    network_observations = create_network_observations(runtime_dataframe, scan_positions)
    network_summary = create_network_summary(network_observations)
    route_comparison = pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS)
    if osm_path is not None and Path(osm_path).exists():
        route_comparison = build_wifi_route_from_scan_positions(
            calibration_dataframe,
            scan_positions,
            load_osm_map(osm_path),
            min_matches=2,
        )
    dataset_summary = summarize_dataset(runtime_dataframe, scan_summary)

    clean_path = save_cleaned_data(runtime_dataframe, output_dir / RUNTIME_FILE_NAMES["cleaned_dataframe"])
    scan_path = save_scan_summary(scan_summary, output_dir / RUNTIME_FILE_NAMES["scan_summary"])
    network_observation_path = save_network_observations(
        network_observations,
        output_dir / RUNTIME_FILE_NAMES["network_observations"],
    )
    network_summary_path = save_network_summary(
        network_summary,
        output_dir / RUNTIME_FILE_NAMES["network_summary"],
    )
    access_point_path = save_triangulated_access_points(
        access_points,
        output_dir / RUNTIME_FILE_NAMES["access_points"],
    )
    scan_position_path = save_triangulated_scan_positions(
        scan_positions,
        output_dir / RUNTIME_FILE_NAMES["scan_positions"],
    )
    route_comparison_path = save_route_estimates(
        route_comparison,
        output_dir / RUNTIME_FILE_NAMES["route_comparison"],
    )
    summary_path = save_dataset_summary(dataset_summary, output_dir / RUNTIME_FILE_NAMES["dataset_summary"])

    return {
        "csv_info": csv_info,
        "cleaned_dataframe": runtime_dataframe,
        "calibration_dataframe": calibration_dataframe,
        "scan_summary": scan_summary,
        "network_observations": network_observations,
        "network_summary": network_summary,
        "access_points": access_points,
        "scan_positions": scan_positions,
        "route_comparison": route_comparison,
        "dataset_summary": dataset_summary,
        "output_paths": [
            clean_path,
            scan_path,
            network_observation_path,
            network_summary_path,
            access_point_path,
            scan_position_path,
            route_comparison_path,
            summary_path,
        ],
    }


def load_runtime_data(processed_dir: str | Path) -> dict[str, object]:
    base_dir = Path(processed_dir)
    missing_files = [
        file_name
        for file_name in RUNTIME_FILE_NAMES.values()
        if not (base_dir / file_name).exists()
    ]
    if missing_files:
        missing_text = ", ".join(missing_files)
        raise FileNotFoundError(f"Verarbeitete Artefakte fehlen: {missing_text}")

    cleaned_dataframe = pd.read_csv(base_dir / RUNTIME_FILE_NAMES["cleaned_dataframe"], parse_dates=["timestamp"])
    scan_summary = pd.read_csv(base_dir / RUNTIME_FILE_NAMES["scan_summary"], parse_dates=["timestamp"])
    network_observations = pd.read_csv(base_dir / RUNTIME_FILE_NAMES["network_observations"], parse_dates=["timestamp"])
    network_summary = pd.read_csv(base_dir / RUNTIME_FILE_NAMES["network_summary"])
    access_points = pd.read_csv(base_dir / RUNTIME_FILE_NAMES["access_points"])
    scan_positions = pd.read_csv(base_dir / RUNTIME_FILE_NAMES["scan_positions"], parse_dates=["timestamp"])
    route_comparison_path = base_dir / RUNTIME_FILE_NAMES["route_comparison"]
    if route_comparison_path.exists():
        route_comparison = pd.read_csv(route_comparison_path, parse_dates=["timestamp"])
    else:
        route_comparison = pd.DataFrame()
    dataset_summary = load_dataset_summary(base_dir / RUNTIME_FILE_NAMES["dataset_summary"])

    return {
        "cleaned_dataframe": cleaned_dataframe,
        "scan_summary": scan_summary,
        "network_observations": network_observations,
        "network_summary": network_summary,
        "access_points": access_points,
        "scan_positions": scan_positions,
        "route_comparison": route_comparison,
        "dataset_summary": dataset_summary,
    }


def load_dataset_summary(summary_path: str | Path) -> dict[str, object]:
    path = Path(summary_path)
    summary: dict[str, object] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if ":" not in raw_line or raw_line.startswith("=") or raw_line.startswith("Datensatz-"):
            continue

        key, value = raw_line.split(":", 1)
        parsed_value = value.strip()
        if parsed_value.isdigit():
            summary[key.strip()] = int(parsed_value)
        else:
            summary[key.strip()] = parsed_value

    return summary

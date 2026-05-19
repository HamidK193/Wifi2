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
from src.route_estimation import (
    GPS_ROUTE_COLUMNS,
    ROUTE_ESTIMATE_COLUMNS,
    ROUTE_QUALITY_COLUMNS,
    add_route_quality_flags,
    add_router_quality_metrics,
    build_gps_route_matched,
    build_gps_route_raw,
    build_route_comparison_with_matched_gps,
    build_wifi_route_from_scan_positions,
    build_wknn_route_comparison,
    save_route_estimates,
)
from src.visualize_wifi_data import load_osm_map

RUNTIME_FILE_NAMES = {
    "cleaned_dataframe": "wifi_scans_clean.csv",
    "scan_summary": "scan_summary.csv",
    "network_observations": "network_observations.csv",
    "network_summary": "network_summary.csv",
    "access_points": "triangulated_access_points.csv",
    "scan_positions": "triangulated_scan_positions.csv",
    "route_comparison": "route_comparison.csv",
    "route_comparison_clean": "route_comparison_clean.csv",
    "route_comparison_outliers": "route_comparison_outliers.csv",
    "route_comparison_wknn": "route_comparison_wknn.csv",
    "route_comparison_wknn_clean": "route_comparison_wknn_clean.csv",
    "route_comparison_wknn_outliers": "route_comparison_wknn_outliers.csv",
    "gps_route_raw": "gps_route_raw.csv",
    "gps_route_matched": "gps_route_matched.csv",
    "route_comparison_wknn_matched": "route_comparison_wknn_matched.csv",
    "route_comparison_wknn_matched_clean": "route_comparison_wknn_matched_clean.csv",
    "route_comparison_wknn_matched_outliers": "route_comparison_wknn_matched_outliers.csv",
    "dataset_summary": "dataset_summary.txt",
}
OPTIONAL_RUNTIME_KEYS = {
    "route_comparison",
    "route_comparison_clean",
    "route_comparison_outliers",
    "route_comparison_wknn",
    "route_comparison_wknn_clean",
    "route_comparison_wknn_outliers",
    "gps_route_raw",
    "gps_route_matched",
    "route_comparison_wknn_matched",
    "route_comparison_wknn_matched_clean",
    "route_comparison_wknn_matched_outliers",
}
ROUTE_OUTPUT_KEYS = [
    "route_comparison",
    "route_comparison_clean",
    "route_comparison_outliers",
    "route_comparison_wknn",
    "route_comparison_wknn_clean",
    "route_comparison_wknn_outliers",
    "gps_route_raw",
    "gps_route_matched",
    "route_comparison_wknn_matched",
    "route_comparison_wknn_matched_clean",
    "route_comparison_wknn_matched_outliers",
]


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
    route_outputs = build_route_outputs(
        calibration_dataframe,
        scan_positions,
        network_observations,
        access_points,
        osm_path,
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
    route_paths = save_route_outputs(route_outputs, output_dir)
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
        **route_outputs,
        "dataset_summary": dataset_summary,
        "output_paths": [
            clean_path,
            scan_path,
            network_observation_path,
            network_summary_path,
            access_point_path,
            scan_position_path,
            *route_paths,
            summary_path,
        ],
    }


def load_runtime_data(processed_dir: str | Path) -> dict[str, object]:
    base_dir = Path(processed_dir)
    missing_files = [
        file_name
        for key, file_name in RUNTIME_FILE_NAMES.items()
        if key not in OPTIONAL_RUNTIME_KEYS and not (base_dir / file_name).exists()
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
    route_outputs = load_route_outputs(base_dir)
    dataset_summary = load_dataset_summary(base_dir / RUNTIME_FILE_NAMES["dataset_summary"])

    return {
        "cleaned_dataframe": cleaned_dataframe,
        "scan_summary": scan_summary,
        "network_observations": network_observations,
        "network_summary": network_summary,
        "access_points": access_points,
        "scan_positions": scan_positions,
        **route_outputs,
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


def _load_optional_runtime_csv(
    path: Path,
    *,
    columns: list[str],
    parse_dates: list[str] | None = None,
) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    return pd.read_csv(path, parse_dates=parse_dates)


def build_route_outputs(
    calibration_dataframe: pd.DataFrame,
    scan_positions: pd.DataFrame,
    network_observations: pd.DataFrame,
    access_points: pd.DataFrame,
    osm_path: str | Path | None,
) -> dict[str, pd.DataFrame]:
    outputs = {
        "route_comparison": pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS),
        "route_comparison_clean": pd.DataFrame(columns=ROUTE_QUALITY_COLUMNS),
        "route_comparison_outliers": pd.DataFrame(columns=ROUTE_QUALITY_COLUMNS),
        "route_comparison_wknn": pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS),
        "route_comparison_wknn_clean": pd.DataFrame(columns=ROUTE_QUALITY_COLUMNS),
        "route_comparison_wknn_outliers": pd.DataFrame(columns=ROUTE_QUALITY_COLUMNS),
        "gps_route_raw": pd.DataFrame(columns=["scan_id", "timestamp", "latitude", "longitude"]),
        "gps_route_matched": pd.DataFrame(columns=GPS_ROUTE_COLUMNS),
        "route_comparison_wknn_matched": pd.DataFrame(columns=ROUTE_ESTIMATE_COLUMNS),
        "route_comparison_wknn_matched_clean": pd.DataFrame(columns=ROUTE_QUALITY_COLUMNS),
        "route_comparison_wknn_matched_outliers": pd.DataFrame(columns=ROUTE_QUALITY_COLUMNS),
    }
    if osm_path is None or not Path(osm_path).exists():
        return outputs

    osm_map = load_osm_map(osm_path)
    outputs["gps_route_raw"] = build_gps_route_raw(calibration_dataframe)
    outputs["gps_route_matched"] = build_gps_route_matched(calibration_dataframe, osm_map)

    route = build_wifi_route_from_scan_positions(
        calibration_dataframe,
        scan_positions,
        osm_map,
        min_matches=2,
    )
    route_quality = add_route_quality_flags(route)
    outputs["route_comparison"] = route
    outputs["route_comparison_clean"], outputs["route_comparison_outliers"] = _split_route_quality(route_quality)

    wknn = build_wknn_route_comparison(calibration_dataframe, osm_map, k=5, min_matches=3)
    wknn = add_router_quality_metrics(wknn, network_observations, access_points)
    wknn_quality = _build_wknn_quality(wknn)
    outputs["route_comparison_wknn"] = wknn
    outputs["route_comparison_wknn_clean"], outputs["route_comparison_wknn_outliers"] = _split_route_quality(
        wknn_quality
    )

    matched_wknn = build_route_comparison_with_matched_gps(
        wknn,
        outputs["gps_route_matched"],
        osm_map,
    )
    matched_wknn = add_router_quality_metrics(matched_wknn, network_observations, access_points)
    matched_quality = _build_wknn_quality(matched_wknn)
    outputs["route_comparison_wknn_matched"] = matched_wknn
    outputs["route_comparison_wknn_matched_clean"], outputs[
        "route_comparison_wknn_matched_outliers"
    ] = _split_route_quality(matched_quality)
    return outputs


def save_route_outputs(route_outputs: dict[str, pd.DataFrame], output_dir: Path) -> list[Path]:
    return [
        save_route_estimates(route_outputs[key], output_dir / RUNTIME_FILE_NAMES[key])
        for key in ROUTE_OUTPUT_KEYS
    ]


def load_route_outputs(base_dir: Path) -> dict[str, pd.DataFrame]:
    columns_by_key = {
        "route_comparison": ROUTE_ESTIMATE_COLUMNS,
        "route_comparison_clean": ROUTE_QUALITY_COLUMNS,
        "route_comparison_outliers": ROUTE_QUALITY_COLUMNS,
        "route_comparison_wknn": ROUTE_ESTIMATE_COLUMNS,
        "route_comparison_wknn_clean": ROUTE_QUALITY_COLUMNS,
        "route_comparison_wknn_outliers": ROUTE_QUALITY_COLUMNS,
        "gps_route_raw": ["scan_id", "timestamp", "latitude", "longitude"],
        "gps_route_matched": GPS_ROUTE_COLUMNS,
        "route_comparison_wknn_matched": ROUTE_ESTIMATE_COLUMNS,
        "route_comparison_wknn_matched_clean": ROUTE_QUALITY_COLUMNS,
        "route_comparison_wknn_matched_outliers": ROUTE_QUALITY_COLUMNS,
    }
    return {
        key: _load_optional_runtime_csv(
            base_dir / RUNTIME_FILE_NAMES[key],
            columns=columns_by_key[key],
            parse_dates=["timestamp"],
        )
        for key in ROUTE_OUTPUT_KEYS
    }


def _build_wknn_quality(route: pd.DataFrame) -> pd.DataFrame:
    return add_route_quality_flags(
        route,
        min_aps=3,
        max_rmse_m=45,
        max_error_m=100,
        max_jump_m=80,
        max_median_router_rmse_m=15,
    )


def _split_route_quality(route_quality: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    clean = route_quality.loc[~route_quality["is_outlier"]].reset_index(drop=True)
    outliers = route_quality.loc[route_quality["is_outlier"]].reset_index(drop=True)
    return clean, outliers

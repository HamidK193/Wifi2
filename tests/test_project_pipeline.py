from pathlib import Path

from src.project_pipeline import load_runtime_data, run_data_pipeline


def test_run_data_pipeline_creates_expected_outputs(triangulation_wigle_csv, tmp_path: Path) -> None:
    pipeline_data = run_data_pipeline(triangulation_wigle_csv, tmp_path)

    assert pipeline_data["dataset_summary"]["rows"] == 12
    assert pipeline_data["dataset_summary"]["scans"] == 4
    assert pipeline_data["dataset_summary"]["unique_network_entities"] == 3
    assert len(pipeline_data["access_points"]) == 3
    assert len(pipeline_data["scan_positions"]) == 4
    assert "route_comparison" in pipeline_data

    output_names = sorted(path.name for path in pipeline_data["output_paths"])
    assert output_names == [
        "dataset_summary.txt",
        "network_observations.csv",
        "network_summary.csv",
        "route_comparison.csv",
        "scan_summary.csv",
        "triangulated_access_points.csv",
        "triangulated_scan_positions.csv",
        "wifi_scans_clean.csv",
    ]

    for output_path in pipeline_data["output_paths"]:
        assert output_path.exists()

    runtime_data = load_runtime_data(tmp_path)
    assert len(runtime_data["access_points"]) == 3
    assert len(runtime_data["scan_positions"]) == 4
    assert "route_comparison" in runtime_data

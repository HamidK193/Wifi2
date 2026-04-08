from pathlib import Path

from src.project_pipeline import run_data_pipeline


def test_run_data_pipeline_creates_expected_outputs(sample_wigle_csv, tmp_path: Path) -> None:
    pipeline_data = run_data_pipeline(sample_wigle_csv, tmp_path)

    assert pipeline_data["dataset_summary"]["rows"] == 3
    assert pipeline_data["dataset_summary"]["scans"] == 2
    assert pipeline_data["dataset_summary"]["unique_network_entities"] == 2

    output_names = sorted(path.name for path in pipeline_data["output_paths"])
    assert output_names == [
        "dataset_summary.txt",
        "network_observations.csv",
        "network_summary.csv",
        "scan_summary.csv",
        "wifi_scans_clean.csv",
    ]

    for output_path in pipeline_data["output_paths"]:
        assert output_path.exists()

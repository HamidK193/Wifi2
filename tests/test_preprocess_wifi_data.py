import pytest

from src.preprocess_wifi_data import clean_wifi_data, create_scan_summary, summarize_dataset


def test_clean_wifi_data_filters_non_wifi_and_invalid_rows(sample_raw_dataframe) -> None:
    cleaned = clean_wifi_data(sample_raw_dataframe)

    assert len(cleaned) == 3
    assert cleaned["network_id"].tolist() == [
        "Alpha | aa:aa:aa:aa:aa:01",
        "Beta | bb:bb:bb:bb:bb:02",
        "Alpha | aa:aa:aa:aa:aa:01",
    ]
    assert cleaned["scan_id"].tolist() == ["scan_01", "scan_01", "scan_02"]


def test_clean_wifi_data_accepts_runtime_rows_without_coordinates(sample_raw_dataframe) -> None:
    runtime_input = sample_raw_dataframe.drop(columns=["CurrentLatitude", "CurrentLongitude", "AccuracyMeters"])

    cleaned = clean_wifi_data(
        runtime_input,
        require_coordinates=False,
        include_coordinates=False,
    )

    assert len(cleaned) == 3
    assert "latitude" not in cleaned.columns
    assert cleaned["scan_id"].tolist() == ["scan_01", "scan_01", "scan_02"]


def test_clean_wifi_data_raises_for_missing_required_columns(sample_raw_dataframe) -> None:
    broken = sample_raw_dataframe.drop(columns=["RSSI"])

    with pytest.raises(ValueError, match="Fehlende Pflichtspalten"):
        clean_wifi_data(broken)


def test_calibration_cleaning_requires_coordinates(sample_raw_dataframe) -> None:
    broken = sample_raw_dataframe.drop(columns=["CurrentLatitude", "CurrentLongitude"])

    with pytest.raises(ValueError, match="Fehlende Pflichtspalten"):
        clean_wifi_data(broken, require_coordinates=True)


def test_scan_summary_and_dataset_summary_are_consistent(sample_raw_dataframe) -> None:
    cleaned = clean_wifi_data(sample_raw_dataframe)
    scan_summary = create_scan_summary(cleaned)
    dataset_summary = summarize_dataset(cleaned, scan_summary)

    assert len(scan_summary) == 2
    assert scan_summary["visible_networks"].tolist() == [2, 1]
    assert dataset_summary["rows"] == 3
    assert dataset_summary["scans"] == 2
    assert dataset_summary["unique_network_entities"] == 2

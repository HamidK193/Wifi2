from src.load_wifi_csv import has_wigle_metadata_row, inspect_wifi_csv, load_wifi_csv


def test_has_wigle_metadata_row_detects_app_header(sample_wigle_csv) -> None:
    assert has_wigle_metadata_row(sample_wigle_csv) is True


def test_inspect_wifi_csv_reports_expected_structure(sample_wigle_csv) -> None:
    csv_info = inspect_wifi_csv(sample_wigle_csv)

    assert csv_info["skip_app_header"] is True
    assert csv_info["data_rows"] == 6
    assert "MAC" in csv_info["columns"]
    assert "Type" in csv_info["columns"]


def test_load_wifi_csv_skips_metadata_row(sample_wigle_csv) -> None:
    dataframe = load_wifi_csv(sample_wigle_csv)

    assert len(dataframe) == 6
    assert list(dataframe.columns)[0] == "MAC"

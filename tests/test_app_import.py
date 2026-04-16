import importlib

import pandas as pd


def test_app_module_imports() -> None:
    app_module = importlib.import_module("app")

    assert app_module.RAW_CSV_PATH.name == "WigleWifi_20260408161721.csv"


def test_all_filters_do_not_show_radius_circles() -> None:
    app_module = importlib.import_module("app")

    assert app_module.should_show_radius_circles("Alle", "Alle", 4508) is False


def test_single_network_allows_overlap_calculation() -> None:
    app_module = importlib.import_module("app")
    filtered_summary = pd.DataFrame(
        [{"network_id": "Alpha | aa:aa:aa:aa:aa:01"}]
    )

    assert app_module.should_calculate_overlap(
        filtered_summary,
        "Alpha",
        "aa:aa:aa:aa:aa:01",
    ) is True


def test_bssid_without_ssid_does_not_calculate_overlap() -> None:
    app_module = importlib.import_module("app")
    filtered_summary = pd.DataFrame(
        [{"network_id": "Alpha | aa:aa:aa:aa:aa:01"}]
    )

    assert app_module.should_calculate_overlap(
        filtered_summary,
        "Alle",
        "aa:aa:aa:aa:aa:01",
    ) is False


def test_multiple_networks_do_not_calculate_global_overlap() -> None:
    app_module = importlib.import_module("app")
    filtered_summary = pd.DataFrame(
        [
            {"network_id": "Alpha | aa:aa:aa:aa:aa:01"},
            {"network_id": "Alpha | bb:bb:bb:bb:bb:02"},
        ]
    )
    observations = pd.DataFrame(
        [
            {"network_id": "Alpha | aa:aa:aa:aa:aa:01"},
            {"network_id": "Alpha | bb:bb:bb:bb:bb:02"},
        ]
    )

    overlap_points = app_module.build_overlap_points(filtered_summary, observations, {})

    assert overlap_points.empty

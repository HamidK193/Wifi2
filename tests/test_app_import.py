import importlib


def test_app_module_imports() -> None:
    app_module = importlib.import_module("app")

    assert app_module.RAW_CSV_PATH.name == "WigleWifi_20260408161721.csv"

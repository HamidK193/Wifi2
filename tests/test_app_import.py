import importlib

import pandas as pd


def test_app_module_imports() -> None:
    app_module = importlib.import_module("app")

    assert app_module.RAW_OSM_PATH.name == "map_innenstadt.osm"


def test_example_input_uses_access_points() -> None:
    app_module = importlib.import_module("app")
    access_points = pd.DataFrame(
        [
            {
                "network_id": "Alpha | aa:aa:aa:aa:aa:01",
                "ssid": "Alpha",
                "bssid": "aa:aa:aa:aa:aa:01",
                "mean_rssi": -68,
            }
        ]
    )

    example = app_module.build_example_input(access_points)

    assert "SSID,BSSID,RSSI" in example
    assert "Alpha,aa:aa:aa:aa:aa:01,-68" in example


def test_router_estimates_need_three_observations() -> None:
    app_module = importlib.import_module("app")
    observations = pd.DataFrame(
        [
            _router_observation("scan_01", 48.88000, 8.70000, -68),
            _router_observation("scan_02", 48.88020, 8.70000, -70),
            _router_observation("scan_03", 48.88010, 8.70025, -69),
        ]
    )

    estimates = app_module.build_router_estimates(observations)
    fallback_estimates = app_module.build_router_estimates(observations.head(2))

    assert len(estimates) == 1
    assert estimates.iloc[0]["bssid"] == "aa:aa:aa:aa:aa:01"
    assert len(fallback_estimates) == 1
    assert fallback_estimates.iloc[0]["quality_flag"] == "fallback"


def test_ssid_color_map_uses_ssid_not_bssid() -> None:
    app_module = importlib.import_module("app")

    colors = app_module.build_ssid_color_map(["Campus", "Campus", "Guest"])

    assert colors["Campus"] == colors["Campus"]
    assert colors["Campus"] != colors["Guest"]


def test_estimate_location_on_road_returns_snapped_result() -> None:
    app_module = importlib.import_module("app")
    access_points = pd.DataFrame(
        [
            _access_point("Alpha", "aa:aa:aa:aa:aa:01", 48.8800, 8.7000),
            _access_point("Beta", "bb:bb:bb:bb:bb:02", 48.8800, 8.7004),
            _access_point("Gamma", "cc:cc:cc:cc:cc:03", 48.8803, 8.7002),
        ]
    )
    osm_map = {
        "bounds": {"minlat": 48.879, "minlon": 8.699, "maxlat": 48.881, "maxlon": 8.701},
        "highways": [[(48.8801, 8.6995), (48.8801, 8.7010)]],
        "walkable_highways": [
            {"highway": "footway", "coordinates": [(48.8801, 8.6995), (48.8801, 8.7010)]}
        ],
        "buildings": [],
    }
    text = "alpha,AA-AA-AA-AA-AA-01,-60\nBeta,bb:bb:bb:bb:bb:02,-61\nGamma,cc:cc:cc:cc:cc:03,-62"

    result, matched, ignored = app_module.estimate_location_on_road(text, access_points, osm_map, min_matches=3)

    assert result is not None
    assert result["snapped"] is True
    assert len(matched) == 3
    assert ignored.empty


def _access_point(ssid: str, bssid: str, latitude: float, longitude: float) -> dict[str, object]:
    return {
        "network_id": f"{ssid} | {bssid}",
        "ssid": ssid,
        "bssid": bssid,
        "latitude": latitude,
        "longitude": longitude,
        "scan_count": 4,
        "total_observations": 4,
        "mean_rssi": -65,
        "min_radius_m": 3,
        "max_radius_m": 30,
        "rmse_m": 5,
        "quality_flag": "good",
    }


def _router_observation(scan_id: str, latitude: float, longitude: float, rssi: int) -> dict[str, object]:
    return {
        "network_id": "Alpha | aa:aa:aa:aa:aa:01",
        "ssid": "Alpha",
        "bssid": "aa:aa:aa:aa:aa:01",
        "scan_id": scan_id,
        "timestamp": "2026-04-08 11:32:44",
        "channel": 6,
        "frequency": 2437,
        "mean_rssi": rssi,
        "strongest_rssi": rssi,
        "observation_count": 1,
        "latitude": latitude,
        "longitude": longitude,
        "accuracy_m": 5,
        "estimated_radius_m": 15,
    }

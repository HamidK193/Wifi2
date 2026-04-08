from pathlib import Path

import pandas as pd
import pytest

from src.load_wifi_csv import load_wifi_csv


@pytest.fixture
def sample_wigle_csv(tmp_path: Path) -> Path:
    csv_content = """WigleWifi-1.6,appRelease=2.104,model=test
MAC,SSID,AuthMode,FirstSeen,Channel,Frequency,RSSI,CurrentLatitude,CurrentLongitude,AltitudeMeters,AccuracyMeters,RCOIs,MfgrId,Type
aa:aa:aa:aa:aa:01,Alpha,Open,2026-04-08 11:32:44,1,2412,-55,48.880000,8.700000,400.0,5.0,,,WIFI
aa:aa:aa:aa:aa:01,Alpha,Open,2026-04-08 11:32:45,1,2412,-60,48.880010,8.700010,400.0,5.0,,,WIFI
bb:bb:bb:bb:bb:02,Beta,WPA2,2026-04-08 11:32:44,6,2437,-70,48.880000,8.700000,400.0,5.0,,,WIFI
cc:cc:cc:cc:cc:03,Gamma,WPA2,1970-01-01 00:00:00,11,2462,-80,48.880020,8.700020,400.0,20.0,,,WIFI
dd:dd:dd:dd:dd:04,Beacon,Open,2026-04-08 11:32:44,,7936,-90,48.880000,8.700000,400.0,5.0,,,BLE
ee:ee:ee:ee:ee:05,,WPA2,2026-04-08 11:32:46,36,5180,-65,48.880030,8.700030,400.0,5.0,,,WIFI
"""
    path = tmp_path / "sample_wigle.csv"
    path.write_text(csv_content, encoding="utf-8")
    return path


@pytest.fixture
def sample_raw_dataframe(sample_wigle_csv: Path) -> pd.DataFrame:
    return load_wifi_csv(sample_wigle_csv)

from difflib import SequenceMatcher
import re

import pandas as pd


MATCH_COLUMNS = ["network_id", "ssid", "bssid", "rssi", "input_ssid", "input_bssid", "ssid_similarity"]
IGNORED_COLUMNS = ["line", "reason"]


def normalize_bssid(value: str) -> str:
    return re.sub(r"[^0-9a-f]", "", str(value).casefold())


def normalize_ssid(value: str) -> str:
    normalized = " ".join(str(value).strip().casefold().split())
    return re.sub(r"[\-_]+", " ", normalized)


def parse_wifi_measurements(text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    ignored: list[dict[str, str]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("ssid"):
            continue

        separator = ";" if ";" in line else ","
        parts = [part.strip() for part in line.split(separator)]
        if len(parts) != 3:
            ignored.append({"line": line, "reason": "Format muss SSID,BSSID,RSSI sein."})
            continue

        ssid, bssid, rssi_text = parts
        try:
            rssi = float(rssi_text)
        except ValueError:
            ignored.append({"line": line, "reason": "RSSI ist keine Zahl."})
            continue

        rows.append({"ssid": ssid, "bssid": bssid, "rssi": rssi, "line": line})

    return pd.DataFrame(rows), pd.DataFrame(ignored, columns=IGNORED_COLUMNS)


def match_wifi_measurements(
    text: str,
    access_points: pd.DataFrame,
    *,
    min_ssid_similarity: float = 0.72,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    parsed, ignored = parse_wifi_measurements(text)
    if parsed.empty or access_points.empty:
        return pd.DataFrame(columns=MATCH_COLUMNS), ignored

    candidates = access_points.copy()
    candidates["_normalized_bssid"] = candidates["bssid"].apply(normalize_bssid)
    candidates["_normalized_ssid"] = candidates["ssid"].apply(normalize_ssid)

    matched_rows: list[dict[str, object]] = []
    ignored_rows = ignored.to_dict("records")

    for row in parsed.itertuples(index=False):
        normalized_bssid = normalize_bssid(row.bssid)
        normalized_ssid = normalize_ssid(row.ssid)
        bssid_candidates = candidates.loc[candidates["_normalized_bssid"] == normalized_bssid].copy()

        if bssid_candidates.empty:
            ignored_rows.append({"line": row.line, "reason": "BSSID wurde nicht in den kalibrierten APs gefunden."})
            continue

        bssid_candidates["_ssid_similarity"] = bssid_candidates["_normalized_ssid"].apply(
            lambda known_ssid: SequenceMatcher(None, normalized_ssid, known_ssid).ratio()
        )
        best = bssid_candidates.sort_values(["_ssid_similarity", "scan_count"], ascending=[False, False]).iloc[0]

        if float(best["_ssid_similarity"]) < min_ssid_similarity:
            ignored_rows.append({"line": row.line, "reason": "SSID ist zu unähnlich zur bekannten BSSID."})
            continue

        matched_rows.append(
            {
                "network_id": best["network_id"],
                "ssid": best["ssid"],
                "bssid": best["bssid"],
                "rssi": float(row.rssi),
                "input_ssid": row.ssid,
                "input_bssid": row.bssid,
                "ssid_similarity": float(best["_ssid_similarity"]),
            }
        )

    return pd.DataFrame(matched_rows, columns=MATCH_COLUMNS), pd.DataFrame(ignored_rows, columns=IGNORED_COLUMNS)

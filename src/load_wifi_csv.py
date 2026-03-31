from pathlib import Path

import pandas as pd

WIGLE_PREFIX = "WigleWifi-"


def has_wigle_metadata_row(file_path: str | Path) -> bool:
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as file:
        first_line = file.readline().strip()

    return first_line.startswith(WIGLE_PREFIX)


def inspect_wifi_csv(file_path: str | Path) -> dict[str, object]:
    path = Path(file_path)
    skip_app_header = has_wigle_metadata_row(path)
    skiprows = 1 if skip_app_header else 0

    with path.open("r", encoding="utf-8") as file:
        total_lines = sum(1 for _ in file)

    columns = pd.read_csv(path, skiprows=skiprows, nrows=0).columns.tolist()
    data_rows = max(total_lines - 1 - skiprows, 0)

    return {
        "file_name": path.name,
        "skip_app_header": skip_app_header,
        "total_lines": total_lines,
        "data_rows": data_rows,
        "columns": columns,
    }


def load_wifi_csv(
    file_path: str | Path,
    skip_app_header: bool | None = None,
) -> pd.DataFrame:
    path = Path(file_path)

    if skip_app_header is None:
        skip_app_header = has_wigle_metadata_row(path)

    skiprows = 1 if skip_app_header else 0
    return pd.read_csv(path, skiprows=skiprows)


def print_csv_overview(csv_info: dict[str, object]) -> None:
    print("CSV-Ueberblick:")
    print(f"- Datei: {csv_info['file_name']}")
    print(f"- Wigle-Metazeile erkannt: {csv_info['skip_app_header']}")
    print(f"- Gesamtzeilen: {csv_info['total_lines']}")
    print(f"- Datenzeilen: {csv_info['data_rows']}")
    print("- Spalten:")
    for column_name in csv_info["columns"]:
        print(f"  - {column_name}")

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def _import_pandas():
    try:
        import pandas as pd
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "pandas wird fuer das Einlesen von WiFi-CSV-Dateien benoetigt. "
            "Installiere es zum Beispiel mit: pip install pandas"
        ) from error

    return pd


def load_wifi_csv(
    file_path: str | Path,
    skip_first_row: bool = False,
    **read_csv_kwargs,
) -> "pd.DataFrame":
    """Laedt eine WiFi-CSV-Datei und gibt ein DataFrame zurueck."""
    pd = _import_pandas()
    path = Path(file_path)
    skiprows = 1 if skip_first_row else 0

    dataframe = pd.read_csv(path, skiprows=skiprows, **read_csv_kwargs)
    return dataframe


def get_column_names(dataframe: "pd.DataFrame") -> list[str]:
    """Gibt die Spaltennamen des DataFrames als Liste zurueck."""
    return dataframe.columns.tolist()


def print_column_names(dataframe: "pd.DataFrame") -> None:
    """Gibt die Spaltennamen gut lesbar auf der Konsole aus."""
    print("Gefundene Spalten:")
    for column_name in get_column_names(dataframe):
        print(f"- {column_name}")

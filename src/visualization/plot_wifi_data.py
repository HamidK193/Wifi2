from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def summarize_rssi_column(
    dataframe: "pd.DataFrame",
    column_name: str = "RSSI",
) -> "pd.Series":
    """Gibt eine einfache Beschreibung einer RSSI-Spalte zurueck."""
    if column_name not in dataframe.columns:
        raise ValueError(f"Spalte nicht gefunden: {column_name}")

    return dataframe[column_name].describe()

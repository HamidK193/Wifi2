from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def rename_columns(
    dataframe: "pd.DataFrame",
    column_mapping: dict[str, str] | None = None,
) -> "pd.DataFrame":
    """Benennt Spalten um, wenn ein Mapping uebergeben wurde."""
    if not column_mapping:
        return dataframe.copy()

    return dataframe.rename(columns=column_mapping)


def check_missing_values(dataframe: "pd.DataFrame") -> "pd.Series":
    """Zaehlt fehlende Werte pro Spalte."""
    return dataframe.isna().sum()


def select_relevant_columns(
    dataframe: "pd.DataFrame",
    columns: list[str],
) -> "pd.DataFrame":
    """Waehlt nur die uebergebenen relevanten Spalten aus."""
    available_columns = [column for column in columns if column in dataframe.columns]
    return dataframe.loc[:, available_columns].copy()

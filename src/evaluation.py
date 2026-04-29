import pandas as pd

from src.localization_logic import calculate_distance_m

DEFAULT_DISPLAY_RADIUS_M = 60.0
ROUTE_COMPARISON_COLUMNS = [
    "scan_id",
    "actual_latitude",
    "actual_longitude",
    "estimated_latitude",
    "estimated_longitude",
    "matched_access_points",
    "residual_rmse",
    "error_m",
]


def build_route_comparison(actual_scan_summary: pd.DataFrame, estimated_scan_summary: pd.DataFrame) -> pd.DataFrame:
    actual = actual_scan_summary.loc[:, ["scan_id", "latitude", "longitude"]].rename(
        columns={
            "latitude": "actual_latitude",
            "longitude": "actual_longitude",
        }
    )
    estimated_columns = [
        "scan_id",
        "latitude",
        "longitude",
        "matched_access_points",
        "residual_rmse",
    ]
    available_estimated_columns = [column for column in estimated_columns if column in estimated_scan_summary.columns]
    estimated = estimated_scan_summary.loc[:, available_estimated_columns].rename(
        columns={
            "latitude": "estimated_latitude",
            "longitude": "estimated_longitude",
        }
    )

    comparison = actual.merge(estimated, on="scan_id", how="inner")
    if comparison.empty:
        return pd.DataFrame(columns=ROUTE_COMPARISON_COLUMNS)

    comparison["error_m"] = comparison.apply(
        lambda row: calculate_distance_m(
            row["actual_latitude"],
            row["actual_longitude"],
            row["estimated_latitude"],
            row["estimated_longitude"],
            row["actual_latitude"],
        ),
        axis=1,
    )
    return comparison.loc[:, ROUTE_COMPARISON_COLUMNS]


def summarize_route_accuracy(route_comparison: pd.DataFrame) -> dict[str, float | int | None]:
    if route_comparison.empty:
        return {
            "compared_scans": 0,
            "mean_error_m": None,
            "median_error_m": None,
            "max_error_m": None,
        }

    return {
        "compared_scans": int(len(route_comparison)),
        "mean_error_m": float(route_comparison["error_m"].mean()),
        "median_error_m": float(route_comparison["error_m"].median()),
        "max_error_m": float(route_comparison["error_m"].max()),
    }


def filter_points_by_radius(
    center_latitude: float | None,
    center_longitude: float | None,
    dataframe: pd.DataFrame,
    *,
    latitude_column: str = "latitude",
    longitude_column: str = "longitude",
    radius_m: float = DEFAULT_DISPLAY_RADIUS_M,
) -> pd.DataFrame:
    if dataframe.empty or center_latitude is None or center_longitude is None:
        return dataframe.copy()
    if latitude_column not in dataframe.columns or longitude_column not in dataframe.columns:
        return dataframe.copy()

    filtered = dataframe.dropna(subset=[latitude_column, longitude_column]).copy()
    if filtered.empty:
        return filtered

    filtered["_distance_to_center_m"] = filtered.apply(
        lambda row: calculate_distance_m(
            center_latitude,
            center_longitude,
            float(row[latitude_column]),
            float(row[longitude_column]),
            center_latitude,
        ),
        axis=1,
    )
    filtered = filtered.loc[filtered["_distance_to_center_m"] <= radius_m].copy()
    return filtered.drop(columns=["_distance_to_center_m"]).reset_index(drop=True)

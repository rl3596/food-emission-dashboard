"""Raw data cleaning functions ported from Keyword Categorization Tool notebook."""

import pandas as pd
import os
from config import DINING_HALLS, MONTHS

COLUMN_NAMES = [
    "item_id", "pack", "size", "brand", "description",
    "mpc_code", "cw",
    "cases_qty", "cases_total", "cases_avg",
    "splits_qty", "splits_total", "splits_avg",
    "lb", "avg_per_lb", "total_sales",
]

LB_TO_KG = 0.45359237


def pre_cleaning(raw_data_path: str) -> pd.DataFrame:
    """Clean raw data for all dining halls combined.

    Args:
        raw_data_path: Path to a monthly raw Excel file.

    Returns:
        DataFrame with columns: pack, description, cases_qty, lb, total_sales, kg
    """
    df = pd.read_excel(raw_data_path, engine="openpyxl", header=7, usecols="A:P")
    df.columns = COLUMN_NAMES
    df = df.dropna(axis=1, how="all")
    df = df.dropna(how="all")

    # Drop totals and count rows
    df = df[
        ~df.apply(
            lambda r: r.astype(str).str.contains("Totals For|Count:", regex=True).any(),
            axis=1,
        )
    ]

    # Drop dining-hall header rows (empty description)
    df = df[df["description"].notna() & (df["description"].astype(str).str.strip() != "")]
    df = df.reset_index(drop=True)

    df_select = df[["pack", "description", "cases_qty", "lb", "total_sales"]].copy()
    df_select["lb"] = pd.to_numeric(df_select["lb"], errors="coerce")
    df_select["kg"] = df_select["lb"] * LB_TO_KG
    df_select = df_select.loc[df_select["total_sales"].astype(float) >= 0]
    return df_select


def pre_cleaning_dininghall(raw_data_path: str, dining_hall_name: str) -> pd.DataFrame:
    """Clean raw data for a specific dining hall.

    Args:
        raw_data_path: Path to a monthly raw Excel file.
        dining_hall_name: Canonical dining hall name (key in DINING_HALLS).

    Returns:
        DataFrame with columns: pack, description, cases_qty, lb, total_sales, dining_hall, kg
    """
    df = pd.read_excel(raw_data_path, engine="openpyxl", header=6, usecols="A:P")
    df.columns = COLUMN_NAMES

    first_col = df.columns[0]
    other_cols = df.columns[1:]

    # Identify dining-hall name rows (only first column has a value)
    is_name_row = df[first_col].notna() & df[other_cols].isna().all(axis=1)
    df["dining_hall"] = df[first_col].where(is_name_row)
    df["dining_hall"] = df["dining_hall"].ffill()

    # Remove name rows and total rows
    is_total_row = df.apply(
        lambda r: r.astype(str)
        .str.contains("Totals For|Count:", regex=True, na=False)
        .any(),
        axis=1,
    )
    df_items = df[~is_name_row & ~is_total_row].reset_index(drop=True)

    # Filter to target dining hall
    search_values = DINING_HALLS[dining_hall_name]
    pattern = "|".join(search_values)
    df_dining = df_items[
        df_items["dining_hall"].str.contains(pattern, case=False, na=False)
    ]

    df_select = df_dining[
        ["pack", "description", "cases_qty", "lb", "total_sales", "dining_hall"]
    ].copy()
    df_select["lb"] = pd.to_numeric(df_select["lb"], errors="coerce")
    df_select["kg"] = df_select["lb"] * LB_TO_KG
    df_select = df_select.loc[df_select["total_sales"].astype(float) >= 0]
    return df_select


def combined_data(
    raw_dir: str,
    year: int,
    start_month: int,
    end_month: int,
    dining_hall: str = None,
) -> pd.DataFrame:
    """Combine monthly raw data into a single DataFrame.

    Args:
        raw_dir: Directory containing RAW_YYYY_MMM.xlsx files.
        year: Data year.
        start_month: Start month (1-12).
        end_month: End month (1-12, inclusive).
        dining_hall: Optional dining hall name to filter.

    Returns:
        Combined DataFrame across all specified months.
    """
    month_names = MONTHS[start_month - 1 : end_month]
    paths = [os.path.join(raw_dir, f"RAW_{year}_{m}.xlsx") for m in month_names]

    # Filter to only existing files
    paths = [p for p in paths if os.path.exists(p)]
    if not paths:
        return pd.DataFrame()

    if dining_hall is None:
        dfs = [pre_cleaning(p) for p in paths]
    else:
        dfs = [pre_cleaning_dininghall(p, dining_hall) for p in paths]

    return pd.concat(dfs, ignore_index=True)

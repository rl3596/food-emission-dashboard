"""Meals served data loader."""

import pandas as pd
import os
from config import MEALS_DIR


def load_meals_data(meals_excel_path: str = None) -> pd.DataFrame:
    """Load and parse meals served data from Excel.

    Args:
        meals_excel_path: Path to the Dining Meals Served Excel file.
                          If None, looks in the data/meals directory.

    Returns:
        DataFrame with columns: month, year, and one column per dining hall,
        plus a total_dining column.
    """
    if meals_excel_path is None:
        # Look for the file in the meals directory
        for f in os.listdir(MEALS_DIR):
            if f.endswith(".xlsx") and "meals" in f.lower():
                meals_excel_path = os.path.join(MEALS_DIR, f)
                break
    if meals_excel_path is None:
        return pd.DataFrame()

    # Try the "meals with 2025" sheet first, fall back to "Meals Served"
    try:
        df = pd.read_excel(meals_excel_path, sheet_name="meals with 2025", engine="openpyxl", header=3)
    except Exception:
        df = pd.read_excel(meals_excel_path, sheet_name="Meals Served", engine="openpyxl", header=3)

    # Clean up column names
    df.columns = [str(c).strip() for c in df.columns]

    # Drop fully empty rows
    df = df.dropna(how="all")

    # The first column should be month labels
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "period"})

    # Filter to rows that look like month data (not headers or totals)
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    df = df[df["period"].astype(str).str.strip().isin(month_names)]
    df = df.reset_index(drop=True)

    return df


def get_meals_summary(df: pd.DataFrame) -> dict:
    """Compute summary statistics from meals data.

    Returns dict with yearly totals and per-hall breakdowns.
    """
    if df.empty:
        return {}

    # Find the Total Dining column
    total_col = None
    for col in df.columns:
        if "total" in str(col).lower() and "dining" in str(col).lower():
            total_col = col
            break

    if total_col is None:
        # Use the last numeric column
        numeric_cols = df.select_dtypes(include="number").columns
        total_col = numeric_cols[-1] if len(numeric_cols) > 0 else None

    summary = {
        "total_column": total_col,
        "total_all_time": df[total_col].sum() if total_col else 0,
    }

    return summary

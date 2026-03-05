"""Staging and commit logic for the two-step upload workflow.

Records flow:  Upload -> Stage (preview) -> Commit (update dashboard)
               or       Upload -> Stage (preview) -> Cancel (discard)

Data management:  List committed records -> Delete -> Recompute emissions

Recompute now produces three output files:
  - emissions_summary.json   (year-keyed annual totals)
  - monthly_emissions.json   (per-month breakdowns for years with month data)
  - ruminant_data.json       (ruminant meat procurement by year)
"""

import json
import os
import uuid
from datetime import datetime

import pandas as pd

from config import STAGING_DIR, COMMITTED_DIR, RESULTS_DIR, MONTHS
from pipeline.emission_calc import load_emission_factors, process_dataframe, compute_summary


# Ruminant meat categories (from categorization.py / emission_factors.json)
RUMINANT_CATEGORIES = ["Beef & buffalo meat", "Lamb/mutton & goat meat"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_id(prefix: str) -> str:
    """Generate a unique ID like stg_20260302_153045_a1b2c3."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{short_uuid}"


def _ensure_dirs():
    """Create staging / committed / results dirs if missing."""
    for d in (STAGING_DIR, COMMITTED_DIR, RESULTS_DIR):
        os.makedirs(d, exist_ok=True)


def _infer_months_from_filenames(filenames: list[str]) -> list[int] | None:
    """Try to infer month numbers from RAW_YYYY_MMM.xlsx-style filenames.

    Returns sorted list of month ints (1-12) or None if no months found.
    """
    months = []
    for fn in filenames:
        fn_upper = fn.upper()
        for i, month_name in enumerate(MONTHS):
            if f"_{month_name}." in fn_upper or f"_{month_name}_" in fn_upper:
                months.append(i + 1)
                break
    return sorted(set(months)) if months else None


def _split_df_by_months(df: pd.DataFrame, months: list[int]) -> dict[int, pd.DataFrame]:
    """Split a DataFrame into per-month DataFrames.

    If the DataFrame has a 'month' column, group by it.
    Otherwise, divide rows proportionally among the given months.
    """
    if "month" in df.columns:
        result = {}
        for m in months:
            mdf = df[df["month"] == m]
            if not mdf.empty:
                result[m] = mdf
        return result

    # Fallback: divide rows proportionally
    n = len(months)
    if n == 0:
        return {}
    chunk_size = len(df) // n if n > 0 else len(df)
    result = {}
    for i, m in enumerate(months):
        start = i * chunk_size
        end = start + chunk_size if i < n - 1 else len(df)
        result[m] = df.iloc[start:end]
    return result


# ---------------------------------------------------------------------------
# Staging operations
# ---------------------------------------------------------------------------

def save_to_staging(df: pd.DataFrame, year: int, scope: str,
                    filenames: list[str], months: list[int] | None = None) -> dict:
    """Save a processed (cleaned + categorised) DataFrame to staging.

    Creates:
      - data/staging/{staging_id}.json   (metadata)
      - data/staging/{staging_id}_data.csv  (row-level data)

    Args:
        df: Cleaned and categorised DataFrame with 'category', 'kg', etc.
        year: Data year (e.g., 2026).
        scope: "all" or specific dining hall.
        filenames: Original uploaded filenames.
        months: List of month numbers (1-12) this upload covers, or None.

    Returns the metadata dict.
    """
    _ensure_dirs()
    staging_id = _generate_id("stg")

    # Category summary for preview
    cat_summary = (
        df.groupby("category")
        .agg(items=("description", "count"), total_kg=("kg", "sum"))
        .sort_values("total_kg", ascending=False)
        .reset_index()
    )
    cat_dict = {
        row["category"]: {"items": int(row["items"]), "total_kg": round(row["total_kg"], 2)}
        for _, row in cat_summary.iterrows()
    }

    uncat = cat_summary[cat_summary["category"] == "Uncategorized"]
    uncat_count = int(uncat["items"].values[0]) if not uncat.empty else 0
    uncat_kg = round(float(uncat["total_kg"].values[0]), 2) if not uncat.empty else 0.0

    metadata = {
        "staging_id": staging_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "year": int(year),
        "months": months,
        "scope": scope,
        "filenames": filenames,
        "total_items": len(df),
        "total_kg": round(float(df["kg"].sum()), 2),
        "uncategorized_count": uncat_count,
        "uncategorized_kg": uncat_kg,
        "category_summary": cat_dict,
        "status": "pending",
    }

    # Write metadata JSON
    meta_path = os.path.join(STAGING_DIR, f"{staging_id}.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Write row-level CSV
    csv_path = os.path.join(STAGING_DIR, f"{staging_id}_data.csv")
    df.to_csv(csv_path, index=False)

    return metadata


def load_staging(staging_id: str) -> tuple[dict, pd.DataFrame]:
    """Load a staging record and its DataFrame."""
    meta_path = os.path.join(STAGING_DIR, f"{staging_id}.json")
    csv_path = os.path.join(STAGING_DIR, f"{staging_id}_data.csv")

    with open(meta_path, "r") as f:
        metadata = json.load(f)

    df = pd.read_csv(csv_path)
    return metadata, df


def list_staging() -> list[dict]:
    """Return all pending staging records sorted by created_at desc."""
    _ensure_dirs()
    records = []
    for fname in os.listdir(STAGING_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(STAGING_DIR, fname), "r") as f:
                records.append(json.load(f))
    records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return records


def delete_staging(staging_id: str) -> bool:
    """Delete a staging record (cancel upload)."""
    meta_path = os.path.join(STAGING_DIR, f"{staging_id}.json")
    csv_path = os.path.join(STAGING_DIR, f"{staging_id}_data.csv")
    deleted = False
    for p in (meta_path, csv_path):
        if os.path.exists(p):
            os.remove(p)
            deleted = True
    return deleted


# ---------------------------------------------------------------------------
# Commit operations
# ---------------------------------------------------------------------------

def commit_staging(staging_id: str) -> dict:
    """Commit a staged upload: compute emissions, write to committed/, recompute.

    Returns the committed record metadata.
    """
    _ensure_dirs()
    metadata, df = load_staging(staging_id)

    # Compute emissions
    factors = load_emission_factors()
    category_emissions, summary = process_dataframe(df, factors)

    # Build committed record
    commit_id = _generate_id("cmt")
    committed = {
        **metadata,
        "commit_id": commit_id,
        "committed_at": datetime.now().isoformat(timespec="seconds"),
        "status": "committed",
        "emissions_summary": summary,
    }
    # Replace staging_id key to keep history
    committed.pop("staging_id", None)

    # Write committed JSON
    cmt_meta_path = os.path.join(COMMITTED_DIR, f"{commit_id}.json")
    with open(cmt_meta_path, "w") as f:
        json.dump(committed, f, indent=2)

    # Copy CSV data
    csv_src = os.path.join(STAGING_DIR, f"{staging_id}_data.csv")
    csv_dst = os.path.join(COMMITTED_DIR, f"{commit_id}_data.csv")
    df.to_csv(csv_dst, index=False)

    # Remove staging record
    delete_staging(staging_id)

    # Recompute all derived data
    recompute_emissions()

    return committed


def list_committed() -> list[dict]:
    """Return all committed records sorted by committed_at desc."""
    _ensure_dirs()
    records = []
    for fname in os.listdir(COMMITTED_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(COMMITTED_DIR, fname), "r") as f:
                records.append(json.load(f))
    records.sort(key=lambda r: r.get("committed_at", ""), reverse=True)
    return records


def delete_committed(commit_id: str) -> bool:
    """Delete a committed record and recompute emissions."""
    meta_path = os.path.join(COMMITTED_DIR, f"{commit_id}.json")
    csv_path = os.path.join(COMMITTED_DIR, f"{commit_id}_data.csv")
    deleted = False
    for p in (meta_path, csv_path):
        if os.path.exists(p):
            os.remove(p)
            deleted = True
    if deleted:
        recompute_emissions()
    return deleted


# ---------------------------------------------------------------------------
# Recompute — produces 3 output files
# ---------------------------------------------------------------------------

def recompute_emissions() -> dict:
    """Rebuild all derived data files from committed records.

    Produces:
      1. emissions_summary.json  — year-keyed annual totals (all years)
      2. monthly_emissions.json  — per-month breakdowns for years with month data
      3. ruminant_data.json      — ruminant meat procurement by year

    For years without committed data, existing values in emissions_summary.json
    are preserved (lazy migration for legacy seeded data).

    Returns the full updated annual summary dict.
    """
    _ensure_dirs()

    # Load current summary (preserves legacy years without committed records)
    summary_path = os.path.join(RESULTS_DIR, "emissions_summary.json")
    try:
        with open(summary_path, "r") as f:
            existing = json.load(f)
    except Exception:
        existing = {}

    # Group committed records by year
    committed_records = list_committed()
    by_year: dict[int, list[dict]] = {}
    for rec in committed_records:
        yr = rec["year"]
        by_year.setdefault(yr, []).append(rec)

    factors = load_emission_factors()
    monthly_data = {}
    ruminant_data = {}

    for year, records in by_year.items():
        # Collect all CSVs and determine month coverage
        all_dfs = []
        all_months = set()
        month_dfs: dict[int, list[pd.DataFrame]] = {}

        for rec in records:
            csv_path = os.path.join(COMMITTED_DIR, f"{rec['commit_id']}_data.csv")
            if not os.path.exists(csv_path):
                continue
            df = pd.read_csv(csv_path)
            all_dfs.append(df)

            # Determine months for this record
            rec_months = rec.get("months") or _infer_months_from_filenames(
                rec.get("filenames", [])
            )

            if rec_months:
                all_months.update(rec_months)
                per_month = _split_df_by_months(df, rec_months)
                for m, mdf in per_month.items():
                    month_dfs.setdefault(m, []).append(mdf)

        if not all_dfs:
            continue

        combined = pd.concat(all_dfs, ignore_index=True)
        _, summary = process_dataframe(combined, factors)

        # ── Compute % change from baseline ──
        # Use the first-computed 2023 value as baseline reference
        baseline_carbon = existing.get("2023", {}).get(
            "total_carbon_tCO2e", summary["total_carbon_tCO2e"]
        )
        if baseline_carbon > 0:
            summary["pct_change_from_baseline"] = (
                (summary["total_carbon_tCO2e"] - baseline_carbon) / baseline_carbon
            )
        else:
            summary["pct_change_from_baseline"] = 0

        existing[str(year)] = summary

        # ── Ruminant data ──
        if "category" in combined.columns:
            category_kg = combined.groupby("category")["kg"].sum()
            ruminant_kg = sum(
                float(category_kg.get(cat, 0)) for cat in RUMINANT_CATEGORIES
            )
            total_kg = float(category_kg.sum())
            ruminant_data[str(year)] = {
                "ruminant_kg": round(ruminant_kg, 2),
                "pct_of_total": round(ruminant_kg / total_kg, 4) if total_kg > 0 else 0,
            }

        # ── Monthly emissions data ──
        sorted_months = sorted(all_months)
        if sorted_months:
            monthly_entry = {
                "months_covered": sorted_months,
                "is_complete": len(sorted_months) == 12,
                "monthly": {},
                "ytd_summary": summary,
            }
            for m in sorted_months:
                if m in month_dfs and month_dfs[m]:
                    m_combined = pd.concat(month_dfs[m], ignore_index=True)
                    _, m_summary = process_dataframe(m_combined, factors)
                    monthly_entry["monthly"][str(m)] = m_summary
            monthly_data[str(year)] = monthly_entry

    # ── Write all three output files ──

    with open(summary_path, "w") as f:
        json.dump(existing, f, indent=2)

    monthly_path = os.path.join(RESULTS_DIR, "monthly_emissions.json")
    with open(monthly_path, "w") as f:
        json.dump(monthly_data, f, indent=2)

    ruminant_path = os.path.join(RESULTS_DIR, "ruminant_data.json")
    with open(ruminant_path, "w") as f:
        json.dump(ruminant_data, f, indent=2)

    return existing

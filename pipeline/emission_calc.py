"""Emission calculation engine replicating Cool Food Calculator formulas."""

import json
import os
import pandas as pd
from config import EMISSION_FACTORS_PATH


def load_emission_factors() -> dict:
    """Load emission factors from JSON file."""
    with open(EMISSION_FACTORS_PATH, "r") as f:
        return json.load(f)


def _match_factor_name(category: str, factors: dict) -> str | None:
    """Find matching emission factor key for a category name.

    Handles minor naming differences between categorization and factor names
    (e.g., trailing spaces, 'Legumes (misc.)' vs 'Legumes').
    """
    cat_lower = category.lower().strip()
    for key in factors:
        key_lower = key.lower().strip()
        if cat_lower in key_lower or key_lower in cat_lower:
            return key
    # Try partial match
    for key in factors:
        key_lower = key.lower().strip()
        # Match first significant word
        cat_first = cat_lower.split("(")[0].strip().split("/")[0].strip()
        key_first = key_lower.split("(")[0].strip().split("/")[0].strip()
        if cat_first == key_first:
            return key
    return None


def compute_category_emissions(category_kg: dict, factors: dict = None) -> dict:
    """Compute emissions for each food category.

    Args:
        category_kg: Dict mapping category name to total kg purchased.
        factors: Emission factors dict (loaded from JSON if not provided).

    Returns:
        Dict with per-category emission metrics.
    """
    if factors is None:
        factors = load_emission_factors()

    results = {}
    for category, total_kg in category_kg.items():
        if category == "Uncategorized" or total_kg <= 0:
            continue

        factor_key = _match_factor_name(category, factors)
        if factor_key is None:
            continue

        f = factors[factor_key]
        fbs_to_retail = f["fbs_to_retail"]
        supply_chain = f["supply_chain_kgCO2e_per_kg"]
        carbon_opp = f["carbon_opp_cost_kgCO2e_per_kg"]
        land_use = f["land_use_m2_per_kg"]
        kcal_per_kg = f["kcal_per_kg"]

        # Boneless equivalent (currently all 100% boneless, so identity)
        boneless_kg = total_kg

        # Metric 2: Supply chain emissions (tonnes CO2e)
        metric2 = boneless_kg * supply_chain / 1000

        # Metric 3: Land use (hectares)
        metric3 = boneless_kg * land_use / 10000

        # Metric 4: Carbon opportunity costs (tonnes CO2e)
        metric4 = boneless_kg * carbon_opp / 1000

        # Calories (millions kcal)
        # kcal_per_kg is for fresh product (FBS weight)
        # Convert retail kg to FBS kg: retail_kg / fbs_to_retail
        if fbs_to_retail > 0:
            kcal_millions = (boneless_kg / fbs_to_retail) * kcal_per_kg / 1_000_000
        else:
            kcal_millions = 0

        results[category] = {
            "input_kg": total_kg,
            "boneless_kg": boneless_kg,
            "metric2_supply_chain_tCO2e": metric2,
            "metric3_land_use_ha": metric3,
            "metric4_carbon_opp_tCO2e": metric4,
            "total_carbon_tCO2e": metric2 + metric4,
            "kcal_millions": kcal_millions,
        }

    return results


def compute_summary(category_emissions: dict) -> dict:
    """Compute aggregate summary from per-category emissions.

    Args:
        category_emissions: Output of compute_category_emissions().

    Returns:
        Summary dict with total metrics and normalized values.
    """
    total_kg = sum(v["input_kg"] for v in category_emissions.values())
    total_metric2 = sum(v["metric2_supply_chain_tCO2e"] for v in category_emissions.values())
    total_metric3 = sum(v["metric3_land_use_ha"] for v in category_emissions.values())
    total_metric4 = sum(v["metric4_carbon_opp_tCO2e"] for v in category_emissions.values())
    total_carbon = total_metric2 + total_metric4
    total_kcal = sum(v["kcal_millions"] for v in category_emissions.values())

    # Normalized metrics
    # total_carbon is in tCO2e, total_kcal is in millions kcal
    # 1 tCO2e / 1 million kcal = 1 kg CO2e / 1000 kcal
    per_1000kcal = (total_carbon / total_kcal) if total_kcal > 0 else 0
    # per_kg_food: kg CO2e per kg food
    per_kg_food = (total_carbon * 1000 / total_kg) if total_kg > 0 else 0

    return {
        "total_kg_procured": total_kg,
        "metric2_supply_chain_tCO2e": total_metric2,
        "metric3_land_use_ha": total_metric3,
        "metric4_carbon_opp_tCO2e": total_metric4,
        "total_carbon_tCO2e": total_carbon,
        "total_kcal_millions": total_kcal,
        "per_1000kcal_kgCO2e": per_1000kcal,
        "per_kg_food_kgCO2e": per_kg_food,
    }


def process_dataframe(df: pd.DataFrame, factors: dict = None) -> tuple[dict, dict]:
    """Full pipeline: from categorized DataFrame to emissions.

    Args:
        df: DataFrame with 'category' and 'kg' columns.
        factors: Optional emission factors dict.

    Returns:
        Tuple of (category_emissions, summary).
    """
    if factors is None:
        factors = load_emission_factors()

    # Group by category and sum kg
    category_kg = df.groupby("category")["kg"].sum().to_dict()

    category_emissions = compute_category_emissions(category_kg, factors)
    summary = compute_summary(category_emissions)

    return category_emissions, summary

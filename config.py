"""Configuration constants for the Food Emission Dashboard."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
COMMITTED_DIR = os.path.join(DATA_DIR, "committed")
MEALS_DIR = os.path.join(DATA_DIR, "meals")
EMISSION_FACTORS_PATH = os.path.join(DATA_DIR, "emission_factors.json")

# Dining halls and their raw data identifiers
DINING_HALLS = {
    "John Jay Dining Hall": ["JOHN JAY2019", "JOHN JAY SUB SHOP", "JOHN JAY FAC SHACK"],
    "Ferris Booth Commons": ["FERRIS BTH COMMONS"],
    "Chef Don's Pizza Pi": ["MUDD"],
    "Chef Mike's Sub Shop": ["URIS"],
    "The Fac Shack": ["DINING ROOM, 64 MORNINGSIDE DR"],
    "JJ's Place": ["JJ'S PLACE"],
    "Robert F. Smith Dining Hall": ["PANTRY ON 10, 665W", "COMMONS CAFE, 665 W", "CAFE BUSINESS SCHOOL, 645 W"],
    "Grace Dodge Dining Hall": ["GRACE DODGE DIN HALL"],
    "TC Catering": ["TEACHERS COL CATERING"],
    "Faculty House": ["FACULTY HOUSE"],
    "Butler Library Cafe": ["BUTLER LIBRARY"],
    "Lenfest Cafe": ["LENFEST CAFE"],
    "Uris Cafe": ["LITTLE URIS"],
    "Everett Library Cafe": ["EVERETT CAFE, 502 W"],
}

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# Emission targets (from Cool Food Pledge)
BASELINE_YEAR = 2023
TARGET_YEAR = 2030

# Absolute target: 25% reduction from baseline
ABSOLUTE_BASELINE = 55206.10  # tCO2e in 2023
ABSOLUTE_TARGET = 41404.57    # tCO2e by 2030

# Relative target: 38% reduction from baseline
RELATIVE_BASELINE = 10.66     # kg CO2e per 1000 kcal in 2023
RELATIVE_TARGET = 6.61        # kg CO2e per 1000 kcal by 2030

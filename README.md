# Columbia University Food Emission Dashboard

A web-based dashboard for tracking food-related carbon emissions at Columbia University Dining, built as part of the [Cool Food Pledge](https://www.wri.org/initiatives/cool-food-pledge) commitment and NYC Plant Powered Carbon Challenge (PPCC).

## Overview

Columbia University tracks food procurement data from dining suppliers and calculates food-related emissions using the Cool Food Calculator methodology (World Resources Institute). This dashboard automates the data pipeline and provides interactive visualizations of emission KPIs.

**Key Targets (by 2030):**
- **25% absolute reduction** in food-related emissions (from 55,206 to 41,405 tCO2e)
- **38% relative reduction** in emissions intensity (from 10.66 to 6.61 kg CO2e per 1,000 kcal)

## Features

- **Cover Page** — Landing page with headline KPIs and navigation
- **Background** — Introduction to the Cool Food Pledge, PPCC, and methodology
- **Emission Dashboard** — Year-over-year emission charts, progress gauges toward 2030 targets, ruminant meat trends
- **Demographics** — Meals served data by dining hall, monthly trends, emissions per meal
- **Data Upload** — Drag-and-drop upload for raw monthly procurement Excel files with automatic processing

## Tech Stack

- **Framework:** [Dash](https://dash.plotly.com/) (Python)
- **Charts:** [Plotly](https://plotly.com/python/)
- **Styling:** [dash-bootstrap-components](https://dash-bootstrap-components.opensource.faculty.ai/) (Flatly theme)
- **Data:** Pandas, openpyxl

## Setup

```bash
# Clone the repository
git clone https://github.com/rl3596/food-emission-dashboard.git
cd food-emission-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

The dashboard will be available at `http://127.0.0.1:8050/`.

## Project Structure

```
├── app.py                  # Main Dash application
├── config.py               # Constants, targets, dining hall mappings
├── pages/                  # Dashboard pages
│   ├── cover.py            # Landing page
│   ├── background.py       # Background & methodology
│   ├── dashboard.py        # Emission KPI dashboard
│   ├── demographics.py     # Meals served analytics
│   └── upload.py           # Data upload & processing
├── pipeline/               # Data processing modules
│   ├── cleaning.py         # Raw Excel data cleaning
│   ├── categorization.py   # 56-category food classification
│   ├── emission_calc.py    # Emission computation engine
│   └── meals_loader.py     # Meals served data parser
├── data/                   # Data storage
│   ├── emission_factors.json   # WRI emission factors
│   ├── results/            # Computed emission summaries
│   ├── meals/              # Meals served CSV
│   └── raw/                # Uploaded raw data (gitignored)
└── assets/                 # CSS and static files
```

## Data Pipeline

1. **Raw Data** — Monthly Excel files from food suppliers (item descriptions, weights, quantities)
2. **Cleaning** — Standardize formats, convert lbs to kg, filter valid entries
3. **Categorization** — Keyword matching into 56 Cool Food Calculator categories
4. **Emission Calculation** — Apply WRI emission factors (supply chain + carbon opportunity costs)
5. **Visualization** — Interactive Plotly charts with year-over-year trends and 2030 targets

## Data Sources

- Poore & Nemecek (2018) — Global life cycle assessment data
- Searchinger et al. (2018) — Carbon opportunity costs
- WRI Cool Food Calculator — Emission factors and methodology

# Columbia University Food Emission Dashboard - Implementation Plan

## Context

Columbia University tracks food procurement data from dining suppliers and calculates food-related carbon emissions using the Cool Food Calculator (WRI tool). The current workflow is manual: raw Excel data → Jupyter notebook cleaning/categorization → Excel calculator → Excel charts. This project builds a **web-based dashboard** to automate the pipeline, visualize KPIs, and provide data upload functionality. The app will use **Python Dash (Plotly)** with emission calculations replicated in Python.

---

## Architecture Overview

**Tech Stack**: Python Dash + Plotly + dash-bootstrap-components
**Calculation Engine**: Python (emission factors extracted from Cool Food Calculator)
**Storage**: JSON files + CSV (lightweight, no database needed)
**Deployment**: Local dev server (gunicorn-ready for production)

---

## Project Structure

```
food-emission-dashboard/        # Git repo root (inside the existing folder)
├── app.py                      # Main Dash app entry point
├── requirements.txt
├── .gitignore
├── README.md
│
├── assets/                     # Static files (CSS, images)
│   └── style.css
│
├── pages/                      # Dash multi-page modules
│   ├── cover.py                # Landing page
│   ├── background.py           # Background & intro
│   ├── dashboard.py            # Emission KPI dashboard
│   ├── demographics.py         # Meals served page
│   └── upload.py               # Data upload page
│
├── pipeline/                   # Data processing (ported from notebook)
│   ├── __init__.py
│   ├── cleaning.py             # Raw data cleaning
│   ├── categorization.py       # 56-category keyword matching
│   ├── emission_calc.py        # Emission computation (replaces Excel formulas)
│   └── meals_loader.py         # Meals served data parser
│
├── data/                       # Data storage
│   ├── raw/                    # Uploaded raw monthly Excel files
│   ├── processed/              # Categorized data (CSV)
│   ├── results/                # Computed emissions (JSON)
│   ├── meals/                  # Meals served data
│   └── emission_factors.json   # Extracted from Cool Food Calculator
│
├── config.py                   # Constants, targets, dining hall mappings
│
└── docs/                       # Reference documents (not tracked in git)
    ├── Columbia University PPCC until december copy.pdf
    ├── tracking-progress-toward-cool-food-pledge.pdf
    └── ...other reference files
```

---

## Implementation Steps

### Step 1: Project Setup & GitHub Repo
- Create project directory structure inside `food emission dashboard/`
- Initialize git repo, create `.gitignore` (exclude `data/raw/*.xlsx`, `__pycache__/`, `.DS_Store`, `venv/`)
- Create `requirements.txt`: dash, dash-bootstrap-components, plotly, pandas, openpyxl, gunicorn
- Create GitHub repo using `gh repo create` (GitHub username: **rl3596**)
- Initial commit with scaffolding

### Step 2: Extract Emission Factors from Cool Food Calculator
- **File**: `empty calculator copy.xlsx`, sheet `Env Data and Conversions`
- Write a one-time extraction script to read the ACTIVE columns (supply chain factor, land use, carbon opportunity cost, kcal/kg) for all 56 food categories
- Also extract FBS-to-retail conversion factors and boneless percentage defaults
- Save to `data/emission_factors.json`
- **Validation**: Cross-check extracted values against known results in `FINAL EMISISIONS 2023-2025 UNTIL DECEMBER copy.xlsx`

### Step 3: Port Data Pipeline from Notebook
- **File to port**: `Keyword Categorization Tool copy.ipynb`

**`pipeline/cleaning.py`**: Extract `pre_cleaning()` and `pre_cleaning_dininghall()` functions
- Read Excel with header=7 (all halls) or header=6 (per hall), columns A:P
- Column names: item_id, pack, size, brand, description, mpc_code, cw, cases_qty, cases_total, cases_avg, splits_qty, splits_total, splits_avg, lb, avg_per_lb, total_sales
- Drop "Totals For" / "Count:" rows, empty descriptions
- Convert lb→kg (factor: 0.45359237), filter total_sales >= 0

**`pipeline/categorization.py`**: Extract 56-category dictionary and `add_category()` function
- Keyword include/exclude matching on uppercased descriptions

**`pipeline/emission_calc.py`**: New module replicating Excel calculator formulas
- For each category: `boneless_kg = input_kg` (since boneless % is 100% for all current data)
- `metric2 = boneless_kg * supply_chain_factor / 1000` (tCO2e)
- `metric4 = boneless_kg * carbon_opp_cost_factor / 1000` (tCO2e)
- `total_kcal = boneless_kg * kcal_per_kg / 1_000_000` (millions kcal)
- `per_1000kcal = (metric2 + metric4) / total_kcal * 1000`
- Aggregate across all categories for totals

**`config.py`**: Constants
- Dining halls dict (14 halls with raw name mappings)
- Month names, root paths
- Targets: baseline 2023 = 55,206 tCO2e, 2030 target = 41,404 tCO2e (25% reduction)
- Relative: baseline 10.66 kg CO2e/1000 kcal, 2030 target = 6.61 (38% reduction)

### Step 4: Seed Data Processing
- Run the pipeline on existing data (2023, 2024, 2025) to generate initial results
- Copy raw data files from `2024 data copy/` into `data/raw/`
- Process and save results to `data/results/emissions_summary.json` and `data/results/category_emissions.json`
- **Validation**: Compare computed totals against FINAL EMISSIONS file known values

### Step 5: Dash App Scaffold
- **`app.py`**: Initialize Dash app with Bootstrap theme (e.g., FLATLY or COSMO), multi-page layout with sidebar navigation
- Configure `pages/` directory for automatic page registration
- Navbar with links: Cover | Background | Dashboard | Demographics | Upload

### Step 6: Dashboard Page (Core KPI Page)
- **`pages/dashboard.py`**
- **Dining hall filter**: Dropdown to select "All Dining" or individual hall
- **KPI cards** at top: Total emissions (tCO2e), % change from baseline, per 1000 kcal, total kg procured
- **Chart 1**: Total food-related emissions (tCO2e) year-over-year — stacked bar (metric 2 supply chain + metric 4 carbon opportunity cost) with 2030 target trend line
- **Chart 2**: Emissions per 1000 kcal year-over-year — same structure with relative target line
- **Chart 3**: Food category breakdown — horizontal bar or treemap showing emission contribution by category
- **Chart 4**: Progress gauge — two Plotly indicators showing % progress toward 2030 absolute and relative targets

### Step 7: Cover Page
- **`pages/cover.py`**
- Hero section with project title: "Columbia University Food Emission Dashboard"
- Subtitle: "Tracking Progress Toward the Cool Food Pledge"
- Quick-glance KPI cards (latest year metrics)
- Navigation buttons to Dashboard, Background, Demographics, Upload

### Step 8: Background Page
- **`pages/background.py`**
- Markdown content sections:
  - About the Cool Food Pledge (WRI initiative, 25% reduction target by 2030)
  - Columbia's participation in NYC Plant Powered Carbon Challenge (PPCC)
  - Methodology: data flow from raw procurement → categorization → emission calculation
  - Key findings: beef = ~3% of menu but ~70% of emissions
  - Data sources and references

### Step 9: Demographics Page
- **`pages/demographics.py`**
- **`pipeline/meals_loader.py`**: Parse `Dining Meals Served - Jan23 to Dec24 copy.xlsx`
- **Chart 1**: Monthly meals served trend (line/area chart)
- **Chart 2**: Meals by dining hall (grouped bar)
- **Chart 3**: Year-over-year meal totals with % change
- **Chart 4**: Emissions per meal trend (declining = good)

### Step 10: Upload Page
- **`pages/upload.py`**
- `dcc.Upload` component for drag-and-drop Excel file upload
- Year and month selection dropdowns
- Optional dining hall scope selector
- Processing workflow: upload → save to `data/raw/` → clean → categorize → compute emissions → update results JSON → refresh dashboard
- Display: categorization preview table, uncategorized items flagged, upload history

### Step 11: Polish & GitHub Push
- Responsive CSS styling in `assets/style.css`
- README with setup instructions, project description, screenshots
- Final git commit and push to GitHub

---

## Key Files to Modify/Reference

| File | Purpose |
|------|---------|
| `Keyword Categorization Tool copy.ipynb` | Source for cleaning, categorization, and calculator I/O logic |
| `empty calculator copy.xlsx` | Source for emission factors (Env Data and Conversions sheet) |
| `FINAL EMISISIONS 2023-2025 UNTIL DECEMBER copy.xlsx` | Validation data + graph reference (graphs in report sheet) |
| `Dining Meals Served - Jan23 to Dec24 copy.xlsx` | Meals served data for demographics page |
| `2024 data copy/RAW_2024_*.xlsx` | Reference raw data format |

---

## Verification Plan

1. **Emission calculation accuracy**: Run pipeline on 2023/2024 data and compare against known FINAL EMISSIONS values:
   - 2023 total: ~55,206 tCO2e
   - 2024 total: ~54,612 tCO2e
   - 2023 per 1000 kcal: ~10.66 kg CO2e
2. **Dashboard visual check**: Compare charts against "graphs in report" sheet in FINAL EMISSIONS file
3. **Upload flow**: Upload a sample RAW_2024_JAN.xlsx, verify it processes correctly and dashboard updates
4. **Per-hall filtering**: Select individual dining halls and verify data matches notebook outputs
5. **Run app**: `python app.py` → verify all 5 pages render and navigate correctly

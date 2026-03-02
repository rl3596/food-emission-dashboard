"""Data Upload Page."""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
import json
import os
import sys

dash.register_page(__name__, path="/upload", name="Upload Data")

# Add parent dir to path for pipeline imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.cleaning import pre_cleaning
from pipeline.categorization import add_category
from pipeline.emission_calc import process_dataframe, load_emission_factors
from config import RAW_DIR, RESULTS_DIR, MONTHS


def layout():
    return dbc.Container(
        [
            html.H2("Upload Raw Data", className="section-header mt-4"),
            html.P(
                "Upload monthly raw procurement data files (Excel format). "
                "The system will automatically clean, categorize, and compute emissions.",
                className="text-muted mb-4",
            ),
            # Upload form
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Year", className="fw-bold"),
                            dcc.Dropdown(
                                id="upload-year",
                                options=[{"label": str(y), "value": y} for y in range(2023, 2031)],
                                value=2025,
                                clearable=False,
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Month(s)", className="fw-bold"),
                            dcc.Dropdown(
                                id="upload-months",
                                options=[{"label": m, "value": i + 1} for i, m in enumerate(MONTHS)],
                                multi=True,
                                placeholder="Select month(s)...",
                            ),
                        ],
                        md=5,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Scope", className="fw-bold"),
                            dcc.Dropdown(
                                id="upload-scope",
                                options=[{"label": "All Dining Halls", "value": "all"}],
                                value="all",
                                clearable=False,
                            ),
                        ],
                        md=4,
                    ),
                ],
                className="mb-4",
            ),
            # File upload area
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    [
                        html.I(className="fas fa-cloud-upload-alt", style={"fontSize": "3rem", "color": "#2e86c1"}),
                        html.Div(
                            [
                                html.Span("Drag and drop ", className="fw-bold"),
                                "or ",
                                html.A("click to select", className="text-primary fw-bold"),
                            ],
                            className="mt-3",
                            style={"fontSize": "1.1rem"},
                        ),
                        html.P("Excel files (.xlsx) matching RAW_YYYY_MMM.xlsx format", className="text-muted mt-2"),
                    ]
                ),
                className="upload-area mb-4",
                multiple=True,
            ),
            # Processing status
            dbc.Spinner(
                html.Div(id="upload-status"),
                color="primary",
                type="border",
            ),
            # Results preview
            html.Div(id="upload-results"),
        ],
        className="page-container",
    )


@callback(
    Output("upload-status", "children"),
    Output("upload-results", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-year", "value"),
    State("upload-scope", "value"),
    prevent_initial_call=True,
)
def process_upload(contents_list, filenames, year, scope):
    if contents_list is None:
        return "", ""

    all_dfs = []
    file_reports = []

    for contents, filename in zip(contents_list, filenames):
        # Decode the uploaded file
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        # Save to raw directory
        os.makedirs(RAW_DIR, exist_ok=True)
        save_path = os.path.join(RAW_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(decoded)

        # Process the file
        try:
            df = pd.read_excel(io.BytesIO(decoded), engine="openpyxl", header=7, usecols="A:P")
            df.columns = [
                "item_id", "pack", "size", "brand", "description",
                "mpc_code", "cw",
                "cases_qty", "cases_total", "cases_avg",
                "splits_qty", "splits_total", "splits_avg",
                "lb", "avg_per_lb", "total_sales",
            ]
            df = df.dropna(axis=1, how="all").dropna(how="all")
            df = df[
                ~df.apply(
                    lambda r: r.astype(str).str.contains("Totals For|Count:", regex=True).any(),
                    axis=1,
                )
            ]
            df = df[df["description"].notna() & (df["description"].astype(str).str.strip() != "")]
            df = df.reset_index(drop=True)
            df_select = df[["pack", "description", "cases_qty", "lb", "total_sales"]].copy()
            df_select["lb"] = pd.to_numeric(df_select["lb"], errors="coerce")
            df_select["kg"] = df_select["lb"] * 0.45359237
            df_select = df_select.loc[df_select["total_sales"].astype(float) >= 0]

            # Categorize
            df_select = add_category(df_select)

            all_dfs.append(df_select)
            file_reports.append({"filename": filename, "rows": len(df_select), "status": "success"})
        except Exception as e:
            file_reports.append({"filename": filename, "rows": 0, "status": f"error: {str(e)}"})

    if not all_dfs:
        return dbc.Alert("No files were processed successfully.", color="danger"), ""

    # Combine all uploaded data
    combined = pd.concat(all_dfs, ignore_index=True)

    # Compute emissions
    try:
        factors = load_emission_factors()
        cat_emissions, summary = process_dataframe(combined, factors)
    except Exception as e:
        return dbc.Alert(f"Emission calculation error: {e}", color="danger"), ""

    # Update the emissions summary
    os.makedirs(RESULTS_DIR, exist_ok=True)
    summary_path = os.path.join(RESULTS_DIR, "emissions_summary.json")

    try:
        with open(summary_path, "r") as f:
            existing = json.load(f)
    except Exception:
        existing = {}

    year_str = str(year)

    # Compute % change from baseline
    baseline_carbon = existing.get("2023", {}).get("total_carbon_tCO2e", summary["total_carbon_tCO2e"])
    if baseline_carbon > 0:
        summary["pct_change_from_baseline"] = (summary["total_carbon_tCO2e"] - baseline_carbon) / baseline_carbon
    else:
        summary["pct_change_from_baseline"] = 0

    existing[year_str] = summary

    with open(summary_path, "w") as f:
        json.dump(existing, f, indent=2)

    # Build status message
    status = dbc.Alert(
        [
            html.I(className="fas fa-check-circle me-2"),
            f"Successfully processed {len(file_reports)} file(s) for {year}. "
            f"Total: {len(combined):,} items, {summary['total_kg_procured']:,.0f} kg, "
            f"{summary['total_carbon_tCO2e']:,.0f} tCO2e",
        ],
        color="success",
    )

    # Category summary table
    cat_summary = combined.groupby("category").agg(
        items=("description", "count"),
        total_kg=("kg", "sum"),
    ).sort_values("total_kg", ascending=False).reset_index()

    uncategorized = cat_summary[cat_summary["category"] == "Uncategorized"]

    table = dbc.Table.from_dataframe(
        cat_summary.head(20).round({"total_kg": 1}),
        striped=True,
        bordered=True,
        hover=True,
        size="sm",
        className="mt-3",
    )

    results = html.Div(
        [
            html.H5("Categorization Results", className="fw-bold mt-4 mb-3"),
            table,
            (
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"{len(uncategorized)} uncategorized items "
                        f"({uncategorized['total_kg'].values[0]:,.0f} kg) — "
                        "consider reviewing and updating keyword rules.",
                    ],
                    color="warning",
                    className="mt-3",
                )
                if not uncategorized.empty and uncategorized["items"].values[0] > 0
                else html.Div()
            ),
            # File processing report
            html.H5("File Report", className="fw-bold mt-4 mb-3"),
            dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("File"), html.Th("Rows"), html.Th("Status")])),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(r["filename"]),
                                    html.Td(str(r["rows"])),
                                    html.Td(
                                        dbc.Badge("Success", color="success")
                                        if r["status"] == "success"
                                        else dbc.Badge(r["status"], color="danger")
                                    ),
                                ]
                            )
                            for r in file_reports
                        ]
                    ),
                ],
                striped=True,
                bordered=True,
                size="sm",
            ),
        ]
    )

    return status, results

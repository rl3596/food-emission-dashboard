"""Data Upload Page — Two-step staged workflow.

Step 1: Select year/month/scope and upload Excel files.
        Files are cleaned, categorized, and saved to staging (not yet on dashboard).
Step 2: Preview the processed data (category table, totals, warnings).
        User can Confirm (commit to dashboard) or Cancel (discard).
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
import os
import sys

dash.register_page(__name__, path="/upload", name="Upload Data")

# Add parent dir to path for pipeline imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.cleaning import pre_cleaning
from pipeline.categorization import add_category
from pipeline.staging import save_to_staging, load_staging, delete_staging, commit_staging
from config import RAW_DIR, MONTHS


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def _step_indicator(active_step: int = 1):
    """Visual step indicator for the two-step workflow."""
    return html.Div(
        [
            html.Div(
                [
                    html.Div("1", className="step-number"),
                    html.Span("Upload & Process"),
                ],
                className=f"step {'active' if active_step == 1 else 'completed' if active_step > 1 else 'inactive'}",
            ),
            html.Div(className="step-connector"),
            html.Div(
                [
                    html.Div("2", className="step-number"),
                    html.Span("Review & Confirm"),
                ],
                className=f"step {'active' if active_step == 2 else 'inactive'}",
            ),
        ],
        className="step-indicator mb-4",
    )


def layout():
    return dbc.Container(
        [
            html.H2("Upload Raw Data", className="section-header mt-4"),
            html.P(
                "Upload monthly raw procurement data files (Excel format). "
                "The system will clean, categorize, and let you preview before updating the dashboard.",
                className="text-muted mb-4",
            ),
            # Step indicators (updated dynamically)
            html.Div(id="upload-step-indicator", children=_step_indicator(1)),

            # Hidden store for staging ID
            dcc.Store(id="staging-id-store", data=None),

            # ── Step 1: Upload form ──
            html.Div(
                id="upload-step-1",
                children=[
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
                                html.I(
                                    className="fas fa-cloud-upload-alt",
                                    style={"fontSize": "3rem", "color": "#2e86c1"},
                                ),
                                html.Div(
                                    [
                                        html.Span("Drag and drop ", className="fw-bold"),
                                        "or ",
                                        html.A("click to select", className="text-primary fw-bold"),
                                    ],
                                    className="mt-3",
                                    style={"fontSize": "1.1rem"},
                                ),
                                html.P(
                                    "Excel files (.xlsx) matching RAW_YYYY_MMM.xlsx format",
                                    className="text-muted mt-2",
                                ),
                            ]
                        ),
                        className="upload-area mb-4",
                        multiple=True,
                    ),
                    # Processing spinner
                    dbc.Spinner(
                        html.Div(id="upload-processing-status"),
                        color="primary",
                        type="border",
                    ),
                ],
            ),

            # ── Step 2: Preview & Confirm (hidden by default) ──
            html.Div(
                id="upload-step-2",
                style={"display": "none"},
                children=[
                    html.Div(id="upload-preview"),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Button(
                                    [html.I(className="fas fa-check me-2"), "Confirm & Update Dashboard"],
                                    id="btn-confirm-upload",
                                    color="success",
                                    size="lg",
                                    className="w-100",
                                ),
                                md=6,
                            ),
                            dbc.Col(
                                dbc.Button(
                                    [html.I(className="fas fa-times me-2"), "Cancel Upload"],
                                    id="btn-cancel-upload",
                                    color="danger",
                                    outline=True,
                                    size="lg",
                                    className="w-100",
                                ),
                                md=6,
                            ),
                        ],
                        className="mt-4 mb-4",
                    ),
                ],
            ),

            # ── Status messages (confirm / cancel results) ──
            html.Div(id="upload-final-status"),
        ],
        className="page-container",
    )


# ---------------------------------------------------------------------------
# Callback 1 — Process uploaded files and save to staging
# ---------------------------------------------------------------------------

@callback(
    Output("upload-step-1", "style"),
    Output("upload-step-2", "style"),
    Output("upload-step-indicator", "children"),
    Output("upload-preview", "children"),
    Output("staging-id-store", "data"),
    Output("upload-processing-status", "children"),
    Output("upload-final-status", "children", allow_duplicate=True),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-year", "value"),
    State("upload-scope", "value"),
    prevent_initial_call=True,
)
def process_upload(contents_list, filenames, year, scope):
    """Clean, categorize, and stage uploaded files for preview."""
    if contents_list is None:
        return no_update, no_update, no_update, no_update, no_update, "", ""

    all_dfs = []
    file_reports = []

    for contents, filename in zip(contents_list, filenames):
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        # Save raw file
        os.makedirs(RAW_DIR, exist_ok=True)
        save_path = os.path.join(RAW_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(decoded)

        # Process the file
        try:
            df = pd.read_excel(
                io.BytesIO(decoded), engine="openpyxl", header=7, usecols="A:P"
            )
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
        error_msg = dbc.Alert(
            [html.I(className="fas fa-exclamation-circle me-2"), "No files were processed successfully."],
            color="danger",
        )
        return no_update, no_update, no_update, no_update, None, error_msg, ""

    # Combine and save to staging
    combined = pd.concat(all_dfs, ignore_index=True)
    metadata = save_to_staging(combined, year, scope, filenames)

    # Build preview
    cat_summary = (
        combined.groupby("category")
        .agg(items=("description", "count"), total_kg=("kg", "sum"))
        .sort_values("total_kg", ascending=False)
        .reset_index()
    )

    preview = html.Div(
        [
            # Summary card
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(
                            [html.I(className="fas fa-search me-2"), "Upload Preview"],
                            className="fw-bold mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(f"{metadata['total_items']:,}", className="kpi-value", style={"fontSize": "1.5rem"}),
                                        html.Div("Total Items", className="kpi-label"),
                                    ],
                                    className="text-center",
                                ),
                                dbc.Col(
                                    [
                                        html.Div(f"{metadata['total_kg']:,.0f} kg", className="kpi-value", style={"fontSize": "1.5rem"}),
                                        html.Div("Total Weight", className="kpi-label"),
                                    ],
                                    className="text-center",
                                ),
                                dbc.Col(
                                    [
                                        html.Div(str(year), className="kpi-value", style={"fontSize": "1.5rem"}),
                                        html.Div("Year", className="kpi-label"),
                                    ],
                                    className="text-center",
                                ),
                                dbc.Col(
                                    [
                                        html.Div(
                                            f"{len(file_reports)}",
                                            className="kpi-value",
                                            style={"fontSize": "1.5rem"},
                                        ),
                                        html.Div("Files Processed", className="kpi-label"),
                                    ],
                                    className="text-center",
                                ),
                            ]
                        ),
                    ]
                ),
                className="preview-card mb-4",
            ),
            # Uncategorized warning
            (
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"{metadata['uncategorized_count']} uncategorized items "
                        f"({metadata['uncategorized_kg']:,.0f} kg) — "
                        "these will be excluded from emission calculations.",
                    ],
                    color="warning",
                )
                if metadata["uncategorized_count"] > 0
                else html.Div()
            ),
            # Category table
            html.H5("Category Breakdown", className="fw-bold mt-3 mb-3"),
            dbc.Table.from_dataframe(
                cat_summary.head(20).round({"total_kg": 1}),
                striped=True,
                bordered=True,
                hover=True,
                size="sm",
            ),
            # File report
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

    return (
        {"display": "none"},           # hide step 1
        {"display": "block"},           # show step 2
        _step_indicator(2),             # update step indicator
        preview,                        # preview content
        metadata["staging_id"],         # store staging id
        "",                             # clear processing status
        "",                             # clear final status
    )


# ---------------------------------------------------------------------------
# Callback 2 — Confirm upload (commit to dashboard)
# ---------------------------------------------------------------------------

@callback(
    Output("upload-step-1", "style", allow_duplicate=True),
    Output("upload-step-2", "style", allow_duplicate=True),
    Output("upload-step-indicator", "children", allow_duplicate=True),
    Output("staging-id-store", "data", allow_duplicate=True),
    Output("upload-final-status", "children", allow_duplicate=True),
    Output("upload-data", "contents", allow_duplicate=True),
    Input("btn-confirm-upload", "n_clicks"),
    State("staging-id-store", "data"),
    prevent_initial_call=True,
)
def confirm_upload(n_clicks, staging_id):
    """Commit staged data to the dashboard."""
    if not n_clicks or not staging_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    try:
        committed = commit_staging(staging_id)
        summary = committed.get("emissions_summary", {})
        total_co2 = summary.get("total_carbon_tCO2e", 0)
        total_kg = summary.get("total_kg_procured", 0)

        status = dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                html.Strong("Data committed successfully! "),
                f"Year {committed['year']}: {total_kg:,.0f} kg processed, "
                f"{total_co2:,.0f} tCO2e computed. The dashboard has been updated.",
            ],
            color="success",
            dismissable=True,
        )
    except Exception as e:
        status = dbc.Alert(
            [html.I(className="fas fa-exclamation-circle me-2"), f"Commit error: {e}"],
            color="danger",
            dismissable=True,
        )

    return (
        {"display": "block"},      # show step 1
        {"display": "none"},       # hide step 2
        _step_indicator(1),        # reset step indicator
        None,                      # clear staging id
        status,                    # show result
        None,                      # reset upload component
    )


# ---------------------------------------------------------------------------
# Callback 3 — Cancel upload (discard staging)
# ---------------------------------------------------------------------------

@callback(
    Output("upload-step-1", "style", allow_duplicate=True),
    Output("upload-step-2", "style", allow_duplicate=True),
    Output("upload-step-indicator", "children", allow_duplicate=True),
    Output("staging-id-store", "data", allow_duplicate=True),
    Output("upload-final-status", "children"),
    Output("upload-data", "contents"),
    Input("btn-cancel-upload", "n_clicks"),
    State("staging-id-store", "data"),
    prevent_initial_call=True,
)
def cancel_upload(n_clicks, staging_id):
    """Discard the staged upload."""
    if not n_clicks or not staging_id:
        return no_update, no_update, no_update, no_update, no_update, no_update

    delete_staging(staging_id)

    status = dbc.Alert(
        [
            html.I(className="fas fa-info-circle me-2"),
            "Upload cancelled. The staged data has been discarded. Dashboard data is unchanged.",
        ],
        color="info",
        dismissable=True,
    )

    return (
        {"display": "block"},      # show step 1
        {"display": "none"},       # hide step 2
        _step_indicator(1),        # reset step indicator
        None,                      # clear staging id
        status,                    # show result
        None,                      # reset upload component
    )

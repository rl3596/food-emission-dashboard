"""Data Management Page — View upload history, manage committed and pending records."""

import dash
from dash import html, dcc, callback, Input, Output, State, ALL, no_update, ctx
import dash_bootstrap_components as dbc
import sys
import os

dash.register_page(__name__, path="/data-management", name="Data Management")

# Add parent dir to path for pipeline imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.staging import (
    list_committed,
    list_staging,
    delete_committed,
    delete_staging,
    commit_staging,
)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    return dbc.Container(
        [
            html.H2("Data Management", className="section-header mt-4"),
            html.P(
                "View and manage all uploaded data. You can review pending uploads, "
                "view committed data history, and remove records to recompute emissions.",
                className="text-muted mb-4",
            ),
            # Hidden stores for state management
            dcc.Store(id="dm-delete-target", data=None),
            dcc.Store(id="dm-refresh-trigger", data=0),

            # Pending uploads section
            html.Div(id="dm-pending-section"),

            # Committed uploads section
            html.Div(id="dm-committed-section"),

            # Delete confirmation modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Confirm Deletion")),
                    dbc.ModalBody(
                        "Are you sure you want to delete this committed record? "
                        "The dashboard emissions will be recomputed without this data. "
                        "This action cannot be undone."
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Delete",
                                id="dm-confirm-delete",
                                color="danger",
                                className="me-2",
                            ),
                            dbc.Button(
                                "Cancel",
                                id="dm-cancel-delete",
                                outline=True,
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="dm-delete-modal",
                is_open=False,
                centered=True,
            ),

            # Status message
            html.Div(id="dm-status"),
        ],
        className="page-container",
    )


# ---------------------------------------------------------------------------
# Helper: build UI sections from data
# ---------------------------------------------------------------------------

def _build_pending_section(records):
    """Build the pending uploads card section."""
    if not records:
        return html.Div(
            [
                html.H4(
                    [html.I(className="fas fa-clock me-2"), "Pending Uploads"],
                    className="fw-bold mb-3",
                ),
                dbc.Alert(
                    "No pending uploads. Go to Upload Data to add new data.",
                    color="light",
                    className="text-muted",
                ),
            ],
            className="mb-5",
        )

    cards = []
    for rec in records:
        cards.append(
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6(
                                            f"Year {rec['year']} — {', '.join(rec.get('filenames', []))}",
                                            className="fw-bold mb-1",
                                        ),
                                        html.Small(
                                            f"Created: {rec.get('created_at', 'N/A')} | "
                                            f"{rec['total_items']:,} items | "
                                            f"{rec['total_kg']:,.0f} kg",
                                            className="text-muted",
                                        ),
                                    ],
                                    md=8,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            [html.I(className="fas fa-check me-1"), "Commit"],
                                            id={"type": "btn-commit-pending", "index": rec["staging_id"]},
                                            color="success",
                                            size="sm",
                                            className="me-2",
                                        ),
                                        dbc.Button(
                                            [html.I(className="fas fa-trash me-1"), "Discard"],
                                            id={"type": "btn-discard-pending", "index": rec["staging_id"]},
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                        ),
                                    ],
                                    md=4,
                                    className="text-end",
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
                className="mb-2",
            )
        )

    return html.Div(
        [
            html.H4(
                [html.I(className="fas fa-clock me-2"), f"Pending Uploads ({len(records)})"],
                className="fw-bold mb-3",
            ),
            *cards,
        ],
        className="mb-5",
    )


def _build_committed_section(records):
    """Build the committed uploads table."""
    if not records:
        return html.Div(
            [
                html.H4(
                    [html.I(className="fas fa-database me-2"), "Committed Data"],
                    className="fw-bold mb-3",
                ),
                dbc.Alert(
                    "No committed records yet. Upload and confirm data to see it here.",
                    color="light",
                    className="text-muted",
                ),
            ],
        )

    rows = []
    for rec in records:
        summary = rec.get("emissions_summary", {})
        total_co2 = summary.get("total_carbon_tCO2e", 0)
        total_kg = summary.get("total_kg_procured", 0)

        rows.append(
            html.Tr(
                [
                    html.Td(rec.get("committed_at", "N/A")[:16]),
                    html.Td(str(rec.get("year", ""))),
                    html.Td(", ".join(rec.get("filenames", []))),
                    html.Td(f"{rec.get('total_items', 0):,}"),
                    html.Td(f"{total_kg:,.0f}"),
                    html.Td(f"{total_co2:,.0f}"),
                    html.Td(
                        dbc.Button(
                            [html.I(className="fas fa-trash-alt")],
                            id={"type": "btn-delete-committed", "index": rec["commit_id"]},
                            color="danger",
                            outline=True,
                            size="sm",
                        ),
                        className="text-center",
                    ),
                ]
            )
        )

    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Date"),
                        html.Th("Year"),
                        html.Th("Files"),
                        html.Th("Items"),
                        html.Th("Total kg"),
                        html.Th("tCO2e"),
                        html.Th("", style={"width": "60px"}),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
    )

    return html.Div(
        [
            html.H4(
                [html.I(className="fas fa-database me-2"), f"Committed Data ({len(records)})"],
                className="fw-bold mb-3",
            ),
            table,
        ],
    )


# ---------------------------------------------------------------------------
# Callback: Load / refresh data
# ---------------------------------------------------------------------------

@callback(
    Output("dm-pending-section", "children"),
    Output("dm-committed-section", "children"),
    Input("dm-refresh-trigger", "data"),
)
def refresh_data(_trigger):
    """Load and display pending + committed records."""
    pending = list_staging()
    committed = list_committed()
    return _build_pending_section(pending), _build_committed_section(committed)


# ---------------------------------------------------------------------------
# Callback: Open delete confirmation modal
# ---------------------------------------------------------------------------

@callback(
    Output("dm-delete-modal", "is_open"),
    Output("dm-delete-target", "data"),
    Input({"type": "btn-delete-committed", "index": ALL}, "n_clicks"),
    Input("dm-cancel-delete", "n_clicks"),
    State("dm-delete-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_delete_modal(delete_clicks, cancel_click, is_open):
    """Open or close the delete confirmation modal."""
    triggered = ctx.triggered_id

    # Cancel button
    if triggered == "dm-cancel-delete":
        return False, None

    # Delete button clicked — open modal with target commit_id
    if isinstance(triggered, dict) and triggered.get("type") == "btn-delete-committed":
        # Check if the actual click happened (not just component creation)
        idx = triggered["index"]
        # Find which button was actually clicked
        for click in delete_clicks:
            if click:
                return True, idx
        return no_update, no_update

    return no_update, no_update


# ---------------------------------------------------------------------------
# Callback: Confirm delete committed record
# ---------------------------------------------------------------------------

@callback(
    Output("dm-delete-modal", "is_open", allow_duplicate=True),
    Output("dm-refresh-trigger", "data", allow_duplicate=True),
    Output("dm-status", "children", allow_duplicate=True),
    Input("dm-confirm-delete", "n_clicks"),
    State("dm-delete-target", "data"),
    State("dm-refresh-trigger", "data"),
    prevent_initial_call=True,
)
def confirm_delete(n_clicks, commit_id, current_trigger):
    """Delete a committed record and recompute emissions."""
    if not n_clicks or not commit_id:
        return no_update, no_update, no_update

    try:
        delete_committed(commit_id)
        status = dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                f"Record {commit_id} deleted. Emissions have been recomputed.",
            ],
            color="success",
            dismissable=True,
        )
    except Exception as e:
        status = dbc.Alert(
            [html.I(className="fas fa-exclamation-circle me-2"), f"Delete error: {e}"],
            color="danger",
            dismissable=True,
        )

    return False, (current_trigger or 0) + 1, status


# ---------------------------------------------------------------------------
# Callback: Commit a pending record from data management page
# ---------------------------------------------------------------------------

@callback(
    Output("dm-refresh-trigger", "data", allow_duplicate=True),
    Output("dm-status", "children", allow_duplicate=True),
    Input({"type": "btn-commit-pending", "index": ALL}, "n_clicks"),
    State("dm-refresh-trigger", "data"),
    prevent_initial_call=True,
)
def commit_pending(commit_clicks, current_trigger):
    """Commit a pending staging record."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict) or triggered.get("type") != "btn-commit-pending":
        return no_update, no_update

    # Check if any button was actually clicked
    if not any(c for c in commit_clicks if c):
        return no_update, no_update

    staging_id = triggered["index"]
    try:
        committed = commit_staging(staging_id)
        summary = committed.get("emissions_summary", {})
        status = dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                f"Data committed for year {committed['year']}. "
                f"{summary.get('total_carbon_tCO2e', 0):,.0f} tCO2e computed. Dashboard updated.",
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

    return (current_trigger or 0) + 1, status


# ---------------------------------------------------------------------------
# Callback: Discard a pending record
# ---------------------------------------------------------------------------

@callback(
    Output("dm-refresh-trigger", "data", allow_duplicate=True),
    Output("dm-status", "children"),
    Input({"type": "btn-discard-pending", "index": ALL}, "n_clicks"),
    State("dm-refresh-trigger", "data"),
    prevent_initial_call=True,
)
def discard_pending(discard_clicks, current_trigger):
    """Discard a pending staging record."""
    triggered = ctx.triggered_id
    if not isinstance(triggered, dict) or triggered.get("type") != "btn-discard-pending":
        return no_update, no_update

    if not any(c for c in discard_clicks if c):
        return no_update, no_update

    staging_id = triggered["index"]
    try:
        delete_staging(staging_id)
        status = dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2"),
                "Pending upload discarded.",
            ],
            color="info",
            dismissable=True,
        )
    except Exception as e:
        status = dbc.Alert(
            [html.I(className="fas fa-exclamation-circle me-2"), f"Error: {e}"],
            color="danger",
            dismissable=True,
        )

    return (current_trigger or 0) + 1, status

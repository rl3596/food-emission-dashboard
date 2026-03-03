"""Cover / Landing Page."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import json
import os

dash.register_page(__name__, path="/", name="Home")

# Load latest metrics for hero cards
def _load_latest_metrics():
    results_path = os.path.join(os.path.dirname(__file__), "..", "data", "results", "emissions_summary.json")
    try:
        with open(results_path, "r") as f:
            data = json.load(f)
        latest_year = max(data.keys())
        return data[latest_year], latest_year
    except Exception:
        return {}, "N/A"


def _make_kpi_card(value, label, icon, change=None):
    change_el = html.Div()
    if change is not None:
        css = "kpi-change-negative" if change < 0 else "kpi-change-positive"
        arrow = "fa-arrow-down" if change < 0 else "fa-arrow-up"
        change_el = html.Div(
            [html.I(className=f"fas {arrow} me-1"), f"{abs(change):.1f}% from baseline"],
            className=css,
            style={"fontSize": "0.9rem"},
        )

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(html.I(className=f"fas {icon}"), style={"fontSize": "1.5rem", "color": "#2e86c1", "marginBottom": "8px"}),
                html.Div(value, className="kpi-value"),
                html.Div(label, className="kpi-label"),
                change_el,
            ],
            className="text-center",
        ),
        className="kpi-card",
    )


def _make_nav_card(title, description, icon, href):
    return dbc.Col(
        dcc.Link(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(html.I(className=f"fas {icon}"), className="card-icon"),
                        html.H5(title, className="fw-bold"),
                        html.P(description, className="text-muted mb-0", style={"fontSize": "0.9rem"}),
                    ]
                ),
                className="nav-card",
            ),
            href=href,
            style={"textDecoration": "none"},
        ),
        md=3,
        className="mb-4",
    )


def layout():
    metrics, latest_year = _load_latest_metrics()
    total_carbon = metrics.get("total_carbon_tCO2e", 0)
    per_1000kcal = metrics.get("per_1000kcal_kgCO2e", 0)
    pct_change = metrics.get("pct_change_from_baseline", 0) * 100
    total_kg = metrics.get("total_kg_procured", 0)

    return html.Div(
        [
            # Hero section
            html.Div(
                dbc.Container(
                    [
                        html.H1("Columbia University Food Emission Dashboard"),
                        html.P(
                            "Tracking progress toward the Cool Food Pledge — reducing food-related "
                            "carbon emissions 25% by 2030."
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-chart-line me-2"), "View Dashboard"],
                            href="/dashboard",
                            color="light",
                            size="lg",
                            className="me-3",
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-info-circle me-2"), "Learn More"],
                            href="/background",
                            outline=True,
                            color="light",
                            size="lg",
                        ),
                    ]
                ),
                className="hero-section",
            ),
            # KPI snapshot
            dbc.Container(
                [
                    html.H4(f"Latest Data: {latest_year}", className="text-center text-muted mb-4"),
                    dbc.Row(
                        [
                            dbc.Col(_make_kpi_card(f"{total_carbon:,.0f}", "Total Emissions (tCO2e)", "fa-cloud", pct_change), md=3),
                            dbc.Col(_make_kpi_card(f"{per_1000kcal:.2f}", "kg CO2e / 1000 kcal", "fa-fire"), md=3),
                            dbc.Col(_make_kpi_card(f"{total_kg / 1000:,.0f}", "Total Food (tonnes)", "fa-weight-hanging"), md=3),
                            dbc.Col(_make_kpi_card("41,405", "2030 Target (tCO2e)", "fa-bullseye"), md=3),
                        ],
                        className="mb-5",
                    ),
                    # Navigation cards
                    html.H3("Explore", className="section-header"),
                    dbc.Row(
                        [
                            _make_nav_card(
                                "Background",
                                "Learn about the Cool Food Pledge and Columbia's commitment to reducing food emissions.",
                                "fa-book-open",
                                "/background",
                            ),
                            _make_nav_card(
                                "Emission Dashboard",
                                "View detailed KPIs, year-over-year trends, and progress toward 2030 targets.",
                                "fa-chart-bar",
                                "/dashboard",
                            ),
                            _make_nav_card(
                                "Demographics",
                                "Explore meals served data across dining halls and emissions per meal trends.",
                                "fa-utensils",
                                "/demographics",
                            ),
                            _make_nav_card(
                                "Upload Data",
                                "Upload monthly raw procurement data to update the dashboard.",
                                "fa-upload",
                                "/upload",
                            ),
                            _make_nav_card(
                                "Data Management",
                                "View upload history, manage committed data, and remove records.",
                                "fa-cogs",
                                "/data-management",
                            ),
                        ]
                    ),
                ],
                className="page-container",
            ),
            # Footer
            html.Div(
                dbc.Container(
                    html.P(
                        "Columbia University Dining Services | Cool Food Pledge Signatory | "
                        "NYC Plant Powered Carbon Challenge Participant",
                        className="mb-0",
                    )
                ),
                className="footer",
            ),
        ]
    )

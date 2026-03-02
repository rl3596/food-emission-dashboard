"""Demographics / Meals Served Page."""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import json
import os

dash.register_page(__name__, path="/demographics", name="Demographics")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..")


def _load_meals():
    path = os.path.join(DATA_DIR, "data", "meals", "meals_served.csv")
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _load_emissions():
    path = os.path.join(DATA_DIR, "data", "results", "emissions_summary.json")
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def layout():
    return dbc.Container(
        [
            html.H2("Dining Demographics", className="section-header mt-4"),
            html.Div(id="demo-kpi-cards"),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H5("Monthly Meals Served", className="fw-bold mb-3"),
                                dcc.Graph(id="chart-monthly-meals"),
                            ],
                            className="chart-container",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.H5("Meals by Dining Hall", className="fw-bold mb-3"),
                                dcc.Graph(id="chart-meals-by-hall"),
                            ],
                            className="chart-container",
                        ),
                        md=6,
                    ),
                ],
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H5("Annual Meals Served", className="fw-bold mb-3"),
                                dcc.Graph(id="chart-annual-meals"),
                            ],
                            className="chart-container",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.H5("Emissions per Meal", className="fw-bold mb-3"),
                                dcc.Graph(id="chart-emissions-per-meal"),
                            ],
                            className="chart-container",
                        ),
                        md=6,
                    ),
                ],
            ),
            dcc.Interval(id="demo-load-trigger", interval=999999999, n_intervals=0, max_intervals=1),
        ],
        className="page-container",
    )


@callback(
    Output("demo-kpi-cards", "children"),
    Output("chart-monthly-meals", "figure"),
    Output("chart-meals-by-hall", "figure"),
    Output("chart-annual-meals", "figure"),
    Output("chart-emissions-per-meal", "figure"),
    Input("demo-load-trigger", "n_intervals"),
)
def update_demographics(_):
    df = _load_meals()
    emissions = _load_emissions()

    empty = go.Figure()
    empty.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)

    if df.empty:
        return html.Div("No meals data loaded"), empty, empty, empty, empty

    # Compute annual totals
    annual = df.groupby("year")["Total Dining"].sum()
    years = sorted(annual.index)
    latest_year = years[-1]
    latest_meals = annual[latest_year]

    # Emissions per meal
    emi_per_meal = {}
    for y in years:
        y_str = str(y)
        if y_str in emissions:
            total_carbon = emissions[y_str]["total_carbon_tCO2e"]
            total_meals = annual[y]
            if total_meals > 0:
                emi_per_meal[y] = total_carbon * 1000 / total_meals  # kg CO2e per meal

    # KPI Cards
    kpi_cards = dbc.Row(
        [
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(html.I(className="fas fa-utensils"), style={"fontSize": "1.3rem", "color": "#2e86c1"}),
                html.Div(f"{latest_meals:,.0f}", className="kpi-value"),
                html.Div(f"Meals Served ({latest_year})", className="kpi-label"),
            ], className="text-center py-3"), className="kpi-card"), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(html.I(className="fas fa-chart-line"), style={"fontSize": "1.3rem", "color": "#2e86c1"}),
                html.Div(f"{len(years)}", className="kpi-value"),
                html.Div("Years of Data", className="kpi-label"),
            ], className="text-center py-3"), className="kpi-card"), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(html.I(className="fas fa-leaf"), style={"fontSize": "1.3rem", "color": "#27ae60"}),
                html.Div(
                    f"{emi_per_meal.get(latest_year, 0):.1f}",
                    className="kpi-value",
                ),
                html.Div("kg CO2e / Meal", className="kpi-label"),
            ], className="text-center py-3"), className="kpi-card"), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(html.I(className="fas fa-building"), style={"fontSize": "1.3rem", "color": "#2e86c1"}),
                html.Div("7", className="kpi-value"),
                html.Div("Dining Halls Tracked", className="kpi-label"),
            ], className="text-center py-3"), className="kpi-card"), md=3),
        ],
        className="mb-4",
    )

    # Chart 1: Monthly meals trend
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig_monthly = go.Figure()
    colors = ["#3498db", "#e67e22", "#27ae60", "#9b59b6"]
    for i, yr in enumerate(years):
        yr_data = df[df["year"] == yr].sort_values("month")
        fig_monthly.add_trace(go.Scatter(
            x=[month_names[m - 1] for m in yr_data["month"]],
            y=yr_data["Total Dining"],
            name=str(yr),
            mode="lines+markers",
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=6),
        ))
    fig_monthly.update_layout(
        yaxis_title="Meals Served",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=20, t=40, b=40),
        plot_bgcolor="white",
        height=380,
    )
    fig_monthly.update_yaxes(gridcolor="#eee")

    # Chart 2: Meals by dining hall (stacked bar per year)
    hall_cols = [c for c in df.columns if c not in ["month", "year", "month_name", "Total Dining"]]
    hall_annual = df.groupby("year")[hall_cols].sum()

    fig_halls = go.Figure()
    hall_colors = ["#3498db", "#e67e22", "#27ae60", "#e74c3c", "#9b59b6", "#f1c40f", "#1abc9c"]
    for i, hall in enumerate(hall_cols):
        fig_halls.add_trace(go.Bar(
            x=[str(y) for y in hall_annual.index],
            y=hall_annual[hall],
            name=hall,
            marker_color=hall_colors[i % len(hall_colors)],
        ))
    fig_halls.update_layout(
        barmode="stack",
        yaxis_title="Meals Served",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9)),
        margin=dict(l=50, r=20, t=60, b=40),
        plot_bgcolor="white",
        height=380,
    )
    fig_halls.update_yaxes(gridcolor="#eee")

    # Chart 3: Annual totals bar
    fig_annual = go.Figure()
    fig_annual.add_trace(go.Bar(
        x=[str(y) for y in years],
        y=[annual[y] for y in years],
        marker_color="#2e86c1",
        text=[f"{annual[y]:,.0f}" for y in years],
        textposition="outside",
    ))
    fig_annual.update_layout(
        yaxis_title="Total Meals",
        margin=dict(l=50, r=20, t=40, b=40),
        plot_bgcolor="white",
        height=380,
    )
    fig_annual.update_yaxes(gridcolor="#eee")

    # Chart 4: Emissions per meal trend
    fig_emi_meal = go.Figure()
    if emi_per_meal:
        emi_years = sorted(emi_per_meal.keys())
        fig_emi_meal.add_trace(go.Bar(
            x=[str(y) for y in emi_years],
            y=[emi_per_meal[y] for y in emi_years],
            marker_color="#27ae60",
            text=[f"{emi_per_meal[y]:.1f}" for y in emi_years],
            textposition="outside",
        ))
        fig_emi_meal.update_layout(
            yaxis_title="kg CO2e per Meal",
            margin=dict(l=50, r=20, t=40, b=40),
            plot_bgcolor="white",
            height=380,
        )
        fig_emi_meal.update_yaxes(gridcolor="#eee")
    else:
        fig_emi_meal.add_annotation(
            text="Emission data not available for meal years",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
        )

    return kpi_cards, fig_monthly, fig_halls, fig_annual, fig_emi_meal

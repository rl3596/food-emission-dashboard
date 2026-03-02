"""Emission KPI Dashboard Page."""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json
import os

dash.register_page(__name__, path="/dashboard", name="Dashboard")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "results")


def _load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _make_kpi_card(value, label, change=None, icon="fa-chart-line"):
    change_el = html.Div()
    if change is not None:
        is_good = change < 0  # negative = emissions going down = good
        css = "kpi-change-negative" if is_good else "kpi-change-positive"
        arrow = "fa-arrow-down" if change < 0 else "fa-arrow-up"
        change_el = html.Div(
            [html.I(className=f"fas {arrow} me-1"), f"{abs(change):.2f}% from baseline"],
            className=css,
            style={"fontSize": "0.85rem", "marginTop": "4px"},
        )
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    html.I(className=f"fas {icon}"),
                    style={"fontSize": "1.3rem", "color": "#2e86c1", "marginBottom": "6px"},
                ),
                html.Div(value, className="kpi-value"),
                html.Div(label, className="kpi-label"),
                change_el,
            ],
            className="text-center py-3",
        ),
        className="kpi-card",
    )


def layout():
    return dbc.Container(
        [
            html.H2("Emission Dashboard", className="section-header mt-4"),
            # KPI Cards row
            html.Div(id="dashboard-kpi-cards"),
            # Charts
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.H5("Total Food-Related Emissions", className="fw-bold mb-3"),
                                dcc.Graph(id="chart-total-emissions"),
                            ],
                            className="chart-container",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.H5("Emissions per 1,000 kcal", className="fw-bold mb-3"),
                                dcc.Graph(id="chart-per-1000kcal"),
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
                                html.H5("Progress Toward 2030 Targets", className="fw-bold mb-3"),
                                dcc.Graph(id="chart-progress-gauges"),
                            ],
                            className="chart-container",
                        ),
                        md=6,
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.H5("Ruminant Meat Procurement Trend", className="fw-bold mb-3"),
                                dcc.Graph(id="chart-ruminant-trend"),
                            ],
                            className="chart-container",
                        ),
                        md=6,
                    ),
                ],
            ),
            # Hidden interval trigger to load data
            dcc.Interval(id="dashboard-load-trigger", interval=999999999, n_intervals=0, max_intervals=1),
        ],
        className="page-container",
    )


@callback(
    Output("dashboard-kpi-cards", "children"),
    Output("chart-total-emissions", "figure"),
    Output("chart-per-1000kcal", "figure"),
    Output("chart-progress-gauges", "figure"),
    Output("chart-ruminant-trend", "figure"),
    Input("dashboard-load-trigger", "n_intervals"),
)
def update_dashboard(_):
    emissions = _load_json("emissions_summary.json")
    targets = _load_json("target_trend.json")
    ruminant = _load_json("ruminant_data.json")

    years = sorted(emissions.keys())
    if not years:
        empty = go.Figure()
        empty.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return html.Div("No data loaded"), empty, empty, empty, empty

    latest = emissions[years[-1]]
    pct_change = latest.get("pct_change_from_baseline", 0) * 100

    # KPI Cards
    kpi_cards = dbc.Row(
        [
            dbc.Col(_make_kpi_card(
                f"{latest['total_carbon_tCO2e']:,.0f}",
                "Total Emissions (tCO2e)",
                pct_change,
                "fa-cloud",
            ), md=3),
            dbc.Col(_make_kpi_card(
                f"{latest['per_1000kcal_kgCO2e']:.2f}",
                "kg CO2e / 1,000 kcal",
                icon="fa-fire",
            ), md=3),
            dbc.Col(_make_kpi_card(
                f"{latest['total_kg_procured'] / 1000:,.0f}",
                "Total Food (tonnes)",
                icon="fa-weight-hanging",
            ), md=3),
            dbc.Col(_make_kpi_card(
                f"{latest['metric2_supply_chain_tCO2e']:,.0f}",
                "Supply Chain (tCO2e)",
                icon="fa-truck",
            ), md=3),
        ],
        className="mb-4",
    )

    # Chart 1: Total Emissions YoY
    fig_total = _build_total_emissions_chart(emissions, targets, years)

    # Chart 2: Per 1000 kcal YoY
    fig_kcal = _build_per_1000kcal_chart(emissions, targets, years)

    # Chart 3: Progress gauges
    fig_gauges = _build_progress_gauges(latest)

    # Chart 4: Ruminant trend
    fig_ruminant = _build_ruminant_chart(ruminant)

    return kpi_cards, fig_total, fig_kcal, fig_gauges, fig_ruminant


def _build_total_emissions_chart(emissions, targets, years):
    metric2 = [emissions[y]["metric2_supply_chain_tCO2e"] for y in years]
    metric4 = [emissions[y]["metric4_carbon_opp_tCO2e"] for y in years]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=metric2,
        name="Supply Chain (Metric 2)",
        marker_color="#3498db",
    ))
    fig.add_trace(go.Bar(
        x=years, y=metric4,
        name="Carbon Opp. Cost (Metric 4)",
        marker_color="#1a5276",
    ))

    # Target trend line
    if "absolute" in targets:
        target_years = sorted(targets["absolute"].keys())
        target_vals = [targets["absolute"][y] for y in target_years]
        fig.add_trace(go.Scatter(
            x=target_years, y=target_vals,
            name="2030 Target Trend",
            mode="lines+markers",
            line=dict(color="#e74c3c", width=2, dash="dash"),
            marker=dict(size=6),
        ))

    fig.update_layout(
        barmode="stack",
        yaxis_title="Tonnes CO2e",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=20, t=40, b=40),
        plot_bgcolor="white",
        height=400,
    )
    fig.update_yaxes(gridcolor="#eee")
    return fig


def _build_per_1000kcal_chart(emissions, targets, years):
    per_kcal_m2 = [emissions[y]["metric2_supply_chain_tCO2e"] /
                   emissions[y].get("total_kcal_millions", 1) for y in years]
    per_kcal_m4 = [emissions[y]["metric4_carbon_opp_tCO2e"] /
                   emissions[y].get("total_kcal_millions", 1) for y in years]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=per_kcal_m2,
        name="Supply Chain / 1000 kcal",
        marker_color="#3498db",
    ))
    fig.add_trace(go.Bar(
        x=years, y=per_kcal_m4,
        name="Carbon Opp. Cost / 1000 kcal",
        marker_color="#1a5276",
    ))

    if "relative" in targets:
        target_years = sorted(targets["relative"].keys())
        target_vals = [targets["relative"][y] for y in target_years]
        fig.add_trace(go.Scatter(
            x=target_years, y=target_vals,
            name="2030 Target Trend",
            mode="lines+markers",
            line=dict(color="#e74c3c", width=2, dash="dash"),
            marker=dict(size=6),
        ))

    fig.update_layout(
        barmode="stack",
        yaxis_title="kg CO2e per 1,000 kcal",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=20, t=40, b=40),
        plot_bgcolor="white",
        height=400,
    )
    fig.update_yaxes(gridcolor="#eee")
    return fig


def _build_progress_gauges(latest):
    from plotly.subplots import make_subplots

    baseline_abs = 55206.10
    target_abs = 41404.57
    current_abs = latest["total_carbon_tCO2e"]
    needed_reduction_abs = baseline_abs - target_abs
    actual_reduction_abs = baseline_abs - current_abs
    pct_progress_abs = (actual_reduction_abs / needed_reduction_abs * 100) if needed_reduction_abs > 0 else 0

    baseline_rel = 10.66
    target_rel = 6.61
    current_rel = latest["per_1000kcal_kgCO2e"]
    needed_reduction_rel = baseline_rel - target_rel
    actual_reduction_rel = baseline_rel - current_rel
    pct_progress_rel = (actual_reduction_rel / needed_reduction_rel * 100) if needed_reduction_rel > 0 else 0

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=["Absolute Emissions", "Per 1,000 kcal"],
    )

    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=pct_progress_abs,
        number={"suffix": "%", "font": {"size": 28}},
        delta={"reference": 100, "relative": False, "valueformat": ".0f", "suffix": "% to go"},
        gauge={
            "axis": {"range": [-50, 100], "ticksuffix": "%"},
            "bar": {"color": "#27ae60" if pct_progress_abs > 0 else "#e74c3c"},
            "steps": [
                {"range": [-50, 0], "color": "#fadbd8"},
                {"range": [0, 50], "color": "#fdebd0"},
                {"range": [50, 100], "color": "#d5f5e3"},
            ],
            "threshold": {"line": {"color": "#e74c3c", "width": 3}, "thickness": 0.75, "value": 100},
        },
    ), row=1, col=1)

    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=pct_progress_rel,
        number={"suffix": "%", "font": {"size": 28}},
        delta={"reference": 100, "relative": False, "valueformat": ".0f", "suffix": "% to go"},
        gauge={
            "axis": {"range": [-50, 100], "ticksuffix": "%"},
            "bar": {"color": "#27ae60" if pct_progress_rel > 0 else "#e74c3c"},
            "steps": [
                {"range": [-50, 0], "color": "#fadbd8"},
                {"range": [0, 50], "color": "#fdebd0"},
                {"range": [50, 100], "color": "#d5f5e3"},
            ],
            "threshold": {"line": {"color": "#e74c3c", "width": 3}, "thickness": 0.75, "value": 100},
        },
    ), row=1, col=2)

    fig.update_layout(height=350, margin=dict(l=30, r=30, t=50, b=20))
    return fig


def _build_ruminant_chart(ruminant):
    if not ruminant:
        fig = go.Figure()
        fig.add_annotation(text="No ruminant data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig

    years = sorted(ruminant.keys())
    kg_vals = [ruminant[y]["ruminant_kg"] / 1000 for y in years]
    pct_vals = [ruminant[y]["pct_of_total"] * 100 for y in years]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=kg_vals,
        name="Ruminant Meat (tonnes)",
        marker_color="#e67e22",
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=years, y=pct_vals,
        name="% of Total Procurement",
        mode="lines+markers",
        line=dict(color="#c0392b", width=2),
        marker=dict(size=8),
        yaxis="y2",
    ))

    fig.update_layout(
        yaxis=dict(title="Tonnes", gridcolor="#eee"),
        yaxis2=dict(title="% of Total", overlaying="y", side="right", range=[0, max(pct_vals) * 1.5]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=40, b=40),
        plot_bgcolor="white",
        height=350,
    )
    return fig

"""Background & Introduction Page."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/background", name="Background")


def layout():
    return dbc.Container(
        [
            html.H2("Background", className="section-header mt-4"),
            # Cool Food Pledge
            html.Div(
                [
                    html.H4(
                        [html.I(className="fas fa-globe-americas me-2 text-primary"), "The Cool Food Pledge"],
                        className="fw-bold mb-3",
                    ),
                    dcc.Markdown(
                        """
The **Cool Food Pledge** is an initiative by the [World Resources Institute (WRI)](https://www.wri.org/)
that brings together food service providers committed to reducing the climate impact of the food
they serve. Signatories commit to reducing food-related greenhouse gas (GHG) emissions by **25%
by 2030** (from a baseline year), aligned with what scientists say is needed to meet the goals of the
Paris Agreement.

The pledge focuses on **shifting food offerings toward more climate-friendly options** — not
restricting choice, but making lower-carbon foods the easy, appealing default. This means
reducing the share of ruminant meats (beef and lamb), increasing plant-based options, and
tracking progress with rigorous data.
                        """,
                        style={"lineHeight": "1.8"},
                    ),
                ],
                className="content-section",
            ),
            # Key Metrics
            html.Div(
                [
                    html.H4(
                        [html.I(className="fas fa-chart-pie me-2 text-primary"), "Key Metrics Tracked"],
                        className="fw-bold mb-3",
                    ),
                    dcc.Markdown(
                        """
The Cool Food Calculator tracks **five metrics** based on Poore and Nemecek (2018) life cycle
assessment data:

1. **Metric 1** — Food purchase weight (kg, boneless equivalent) by food type
2. **Metric 2** — Food-related GHG emissions from agricultural supply chains (tonnes CO2e)
3. **Metric 3** — Food-related land use (hectares)
4. **Metric 4** — Food-related carbon opportunity costs (tonnes CO2e)
5. **Metric 5** — Normalized metrics (per kg food, per 1,000 kcal, per meal)

The two primary KPIs for this dashboard are:
- **Total food-related emissions** (Metric 2 + Metric 4) — the absolute carbon footprint
- **Emissions per 1,000 kcal** — the relative intensity, accounting for the nutritional value served
                        """,
                        style={"lineHeight": "1.8"},
                    ),
                ],
                className="content-section",
            ),
            # Targets
            html.Div(
                [
                    html.H4(
                        [html.I(className="fas fa-bullseye me-2 text-primary"), "Reduction Targets"],
                        className="fw-bold mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H2("25%", className="text-primary fw-bold"),
                                            html.P("Absolute Reduction", className="fw-bold"),
                                            html.P(
                                                "From 55,206 tCO2e (2023) to 41,405 tCO2e by 2030",
                                                className="text-muted small",
                                            ),
                                        ],
                                        className="text-center",
                                    ),
                                    className="kpi-card",
                                ),
                                md=6,
                            ),
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H2("38%", className="text-primary fw-bold"),
                                            html.P("Relative Reduction", className="fw-bold"),
                                            html.P(
                                                "From 10.66 to 6.61 kg CO2e per 1,000 kcal by 2030",
                                                className="text-muted small",
                                            ),
                                        ],
                                        className="text-center",
                                    ),
                                    className="kpi-card",
                                ),
                                md=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                ],
                className="content-section",
            ),
            # Columbia's Participation
            html.Div(
                [
                    html.H4(
                        [html.I(className="fas fa-university me-2 text-primary"), "Columbia University's Commitment"],
                        className="fw-bold mb-3",
                    ),
                    dcc.Markdown(
                        """
Columbia University participates in the **NYC Mayor's Plant Powered Carbon Challenge (PPCC)**,
committing to reduce food-related emissions by 25% by 2030. Columbia Dining operates 14 dining
locations across campus, serving over **2 million meals annually**.

**Key findings from Columbia's tracking:**
- Beef represents approximately **3-5% of food procurement by weight** but accounts for roughly
  **40-45% of total food-related carbon emissions**
- Between 2023 and 2024, beef procurement was reduced by **8.58%** (from 100,423 kg to 91,804 kg)
- Plant-based options have been expanded, including items like Mushroom Lentil Bolognese and
  Chickpea Tagine
- Oat milk was adopted as the default milk option in September 2024
                        """,
                        style={"lineHeight": "1.8"},
                    ),
                ],
                className="content-section",
            ),
            # Methodology
            html.Div(
                [
                    html.H4(
                        [html.I(className="fas fa-cogs me-2 text-primary"), "Methodology"],
                        className="fw-bold mb-3",
                    ),
                    dcc.Markdown(
                        """
**Data Pipeline:**

1. **Raw Data Collection** — Monthly procurement data from food suppliers in Excel format,
   containing item descriptions, weights (lbs), quantities, and sales totals
2. **Data Cleaning** — Standardize formats, convert lbs to kg, filter valid entries
3. **Food Categorization** — A custom keyword-matching tool categorizes each food item into
   one of **56 Cool Food Calculator categories** (e.g., "Beef & buffalo meat", "Poultry",
   "Wheat/Rye", "Vegetables") using include/exclude keyword rules
4. **Emission Calculation** — For each category, emissions are computed using WRI emission
   factors (supply chain emissions + carbon opportunity costs per kg)
5. **Visualization** — Results are displayed in this dashboard with year-over-year trends
   and progress toward 2030 targets

**Data Sources:**
- Poore & Nemecek (2018) — Global life cycle assessment data
- Searchinger et al. (2018) — Carbon opportunity costs
- WRI Cool Food Calculator — Emission factors and methodology
                        """,
                        style={"lineHeight": "1.8"},
                    ),
                ],
                className="content-section",
            ),
        ],
        className="page-container",
    )

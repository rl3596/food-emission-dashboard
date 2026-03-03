"""Columbia University Food Emission Dashboard - Main Application."""

import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "Columbia Food Emission Dashboard"

# Navigation bar
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand(
                [
                    html.I(className="fas fa-leaf me-2"),
                    "Columbia Food Emissions",
                ],
                href="/",
                className="fw-bold",
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink("Home", href="/")),
                        dbc.NavItem(dbc.NavLink("Background", href="/background")),
                        dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard")),
                        dbc.NavItem(dbc.NavLink("Demographics", href="/demographics")),
                        dbc.NavItem(dbc.NavLink("Upload Data", href="/upload")),
                        dbc.NavItem(dbc.NavLink("Data Management", href="/data-management")),
                    ],
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    color="dark",
    dark=True,
    sticky="top",
    className="mb-0",
)

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        navbar,
        dash.page_container,
    ]
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)

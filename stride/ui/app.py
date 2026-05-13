import dash
from dash import html


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        title="Stride",
        assets_folder="../assets",
        suppress_callback_exceptions=True,
    )

    app.layout = _layout

    return app


def _layout():
    return html.Div(
        style={
            "fontFamily": "system-ui, sans-serif",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "height": "100vh",
            "background": "#f5f3ee",
            "color": "#1a1a1a",
        },
        children=[
            html.H1("Stride", style={"fontSize": "3rem", "fontWeight": "700", "margin": "0"}),
            html.P(
                "Personal day-lane task board — coming soon.",
                style={"color": "#666", "marginTop": "0.5rem"},
            ),
        ],
    )

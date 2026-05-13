import typer

app = typer.Typer(help="Stride — personal day-lane task board.")


@app.command()
def run(
    port: int = typer.Option(8050, "--port", "-p", help="Port to listen on."),
    debug: bool = typer.Option(False, "--debug", help="Enable Dash debug mode."),
):
    """Start the Stride web app."""
    from stride.ui.app import create_app

    dash_app = create_app()
    dash_app.run(port=port, debug=debug)

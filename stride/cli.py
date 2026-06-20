import typer

app = typer.Typer(help="Stride — personal day-lane task board.")


@app.command()
def run(
    port: int = typer.Option(8050, "--port", "-p", help="Port to listen on."),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind on."),
    debug: bool = typer.Option(False, "--debug", help="Enable Dash debug mode."),
):
    """Start the Stride web app."""
    from stride.ui.app import create_app

    dash_app = create_app()
    dash_app.run(host=host, port=port, debug=debug)


@app.command("create-user")
def create_user_cmd(
    email: str = typer.Option(..., "--email", "-e", help="User's email address."),
    name: str = typer.Option(..., "--name", "-n", help="Display name (e.g. 'Alan')."),
    password: str = typer.Option(
        ..., "--password", "-p", prompt=True, hide_input=True,
        confirmation_prompt=True, help="Password (will prompt if omitted).",
    ),
    admin: bool = typer.Option(False, "--admin", help="Grant admin privileges."),
):
    """Create a user account (admin use only — no self-registration in v1)."""
    from stride.db import app_db, run_migrations
    from stride.services.auth import create_user, get_user_by_email

    run_migrations()
    conn = app_db()

    if get_user_by_email(conn, email) is not None:
        typer.echo(f"[error] A user with email '{email}' already exists.", err=True)
        raise typer.Exit(1)

    if len(password) < 8:
        typer.echo("[error] Password must be at least 8 characters.", err=True)
        raise typer.Exit(1)

    user_id = create_user(conn, email=email, display_name=name, password=password, is_admin=admin)
    role = "admin" if admin else "user"
    typer.echo(f"[ok] Created {role} '{name}' <{email}> — id: {user_id}")

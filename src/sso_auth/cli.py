"""Typer CLI for sso_auth."""

from __future__ import annotations

import getpass

import typer
from rich.console import Console
from rich.table import Table

from sso_auth.client import SsoClient
from sso_auth.logging import setup_default_logging

app = typer.Typer(help="SSO authentication helper for sso.bps.go.id")
console = Console()


def _build_client(username: str) -> SsoClient:
    return SsoClient.from_keyring(username=username)


@app.command()
def login(username: str, save_keyring: bool = True) -> None:
    password = getpass.getpass("Password: ")
    client = SsoClient(username=username, password=password, use_keyring=save_keyring)
    result = client.login()
    console.print(f"Logged in via method: {result.method}")


@app.command()
def logout(username: str) -> None:
    client = _build_client(username)
    client.logout()
    console.print("Logged out and local credentials removed.")


@app.command()
def whoami(username: str) -> None:
    client = _build_client(username)
    if not client.user_info:
        console.print("No cached user profile found.")
        raise typer.Exit(code=1)
    table = Table(title="User Info")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Name", client.user_info.name or "-")
    table.add_row("Email", client.user_info.email or "-")
    table.add_row("Username", client.user_info.preferred_username or client.user_info.username or "-")
    console.print(table)


@app.command()
def token(username: str, refresh_if_needed: bool = True) -> None:
    client = _build_client(username)
    if refresh_if_needed:
        client.ensure_valid()
    if not client.access_token:
        raise typer.Exit(code=1)
    console.print(client.access_token)


@app.command()
def refresh(username: str) -> None:
    client = _build_client(username)
    token_bundle = client.refresh()
    console.print(f"Token refreshed. Expires in: {token_bundle.expires_in}s")


@app.command()
def status(username: str) -> None:
    client = _build_client(username)
    if not client.is_authenticated:
        console.print("Status: unauthenticated")
        return
    expiring = client.user_info is not None and client.access_token != ""
    console.print(f"Status: authenticated (token_present={expiring})")


def run() -> None:
    setup_default_logging()
    app()

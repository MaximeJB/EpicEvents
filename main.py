"""Point d'entrée principal de la CLI Epic Events.

Regroupe toutes les commandes sous un même programme et initialise Sentry.
"""

import os

import click
from dotenv import load_dotenv
import sentry_sdk

from app.views.auth import auth
from app.views.client import client
from app.views.contract import contract
from app.views.event import event
from app.cli_app import menu_principal
from app.views.user import collab

load_dotenv()

sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        send_default_pii=True,
        enable_logs=True,
    )


@click.group()
def cli():
    """Epic Events CRM - Gestion de clients, contrats et événements."""
    pass


cli.add_command(auth)
cli.add_command(client)
cli.add_command(contract)
cli.add_command(collab)
cli.add_command(event)
cli.add_command(menu_principal)


if __name__ == "__main__":
    cli()

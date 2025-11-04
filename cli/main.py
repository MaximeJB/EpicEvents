"""
Point d'entrée principal de la CLI Epic Events.
Regroupe toutes les commandes sous un m�me programme.
"""
import click
from cli.auth_cli import auth
from cli.client_cli import client
from cli.contract_cli import contract
from cli.user_cli import collab
from cli.event_cli import event



@click.group()
def cli():
    """Epic Events CRM - Gestion de clients, contrats et événements."""
    pass

cli.add_command(auth)
cli.add_command(client)
cli.add_command(contract)
cli.add_command(collab)
cli.add_command(event)

if __name__ == "__main__":
    cli()

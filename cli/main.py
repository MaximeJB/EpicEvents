"""
Point d'entrée principal de la CLI Epic Events.
Regroupe toutes les commandes sous un m�me programme.
"""
import click
from cli.auth_cli import auth



@click.group()
def cli():
    """Epic Events CRM - Gestion de clients, contrats et événements."""
    pass

cli.add_command(auth)

if __name__ == "__main__":
    cli()

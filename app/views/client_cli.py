"""Commandes CLI pour la gestion des clients."""
import logging

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.auth import get_current_user
from app.crud.crud_client import create_client, get_client, list_clients, update_client
from app.db import SessionLocal

logger = logging.getLogger(__name__)
console = Console()


@click.group()
def client():
    """Groupe composé de toutes les possibilités de client."""
    pass


@client.command()
def create():
    """Créer un nouveau client.

    Demande les informations du client et crée l'entrée dans la base de données.
    """
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if user is None:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Pas d'utilisateur connecté          │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return
        else:
            name = click.prompt("Entrez le nom du client")
            phone = click.prompt("Entrez le téléphone du client")
            company = click.prompt("Entrez le nom de l'entreprise du client")
            email = click.prompt("Entre l'email du client : ")
            try:
                new_client = create_client(db, current_user=user, name=name, phone=phone, company=company, email=email)
                console.print("\n[green]╭───────────────────────────────────────╮[/green]")
                console.print(f"[green]│ ✓ Client créé : {new_client.name} (ID: {new_client.id}){' ' * (38 - len(f'✓ Client créé : {new_client.name} (ID: {new_client.id})'))}│[/green]")
                console.print("[green]╰───────────────────────────────────────╯[/green]\n")
            except ValueError as e:
                console.print("\n[red]╭───────────────────────────────────────╮[/red]")
                console.print(f"[red]│ ✗ Erreur de valeur : {e}{' ' * (38 - len(f'✗ Erreur de valeur : {e}'))}│[/red]")
                console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            except PermissionError as e:
                console.print("\n[red]╭───────────────────────────────────────╮[/red]")
                console.print(f"[red]│ ✗ Permission refusée : {e}{' ' * (38 - len(f'✗ Permission refusée : {e}'))}│[/red]")
                console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    finally:
        db.close()


@client.command()
def list():
    """Lister les clients.

    Affiche tous les clients accessibles selon le rôle de l'utilisateur.
    """
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if user is None:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Pas d'utilisateur connecté          │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return
        else:
            clients = list_clients(db, user)
            if not clients:
                console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
                console.print("[yellow]│ Aucun client à afficher                │[/yellow]")
                console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
                return
            else:
                table = Table(title="Liste des Clients")
                table.add_column("ID", style="cyan", justify="center")
                table.add_column("Nom", style="green")
                table.add_column("Entreprise", style="yellow")
                table.add_column("Téléphone")
                table.add_column("Email", style="blue")

                for client in clients:
                    table.add_row(
                        str(client.id),
                        client.name,
                        client.company_name,
                        client.phone_number,
                        client.email
                    )

                console.print(table)
    finally:
        db.close()


@client.command()
def update():
    """Mettre à jour un client.

    Permet de modifier les informations d'un client existant.
    """
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if user is None:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Pas d'utilisateur connecté          │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        client_id = click.prompt("Quel est l'ID du client à mettre à jour ?", type=int)

        target_client = get_client(db, client_id)
        if not target_client:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Aucun client trouvé avec cet ID     │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        panel = Panel(
            f"[bold]Nom:[/bold] {target_client.name}\n"
            f"[bold]Entreprise:[/bold] {target_client.company_name}\n"
            f"[bold]Email:[/bold] {target_client.email}\n"
            f"[bold]Téléphone:[/bold] {target_client.phone_number}",
            title="Client actuel",
            border_style="blue"
        )
        console.print(panel)
        console.print("[yellow]Laissez vide pour ne pas modifier un champ[/yellow]\n")

        name = click.prompt("Nouveau nom", default="", show_default=False)
        email = click.prompt("Nouvel email", default="", show_default=False)
        phone = click.prompt("Nouveau téléphone", default="", show_default=False)
        company = click.prompt("Nouvelle entreprise", default="", show_default=False)

        kwargs = {}
        if name:
            kwargs['name'] = name
        if email:
            kwargs['email'] = email
        if phone:
            kwargs['phone'] = phone
        if company:
            kwargs['company'] = company

        if not kwargs:
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ Aucune modification effectuée          │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
            return

        try:
            updated = update_client(db, current_user=user, client_id=client_id, **kwargs)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(f"[green]│ ✓ Client mis à jour : {updated.name} (ID: {updated.id}){' ' * (38 - len(f'✓ Client mis à jour : {updated.name} (ID: {updated.id})'))}│[/green]")
            console.print("[green]╰───────────────────────────────────────╯[/green]\n")
        except ValueError as e:
            logger.error("Exception levé lors de la mise à jour d'un client")
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print(f"[red]│ ✗ Erreur : {e}{' ' * (38 - len(f'✗ Erreur : {e}'))}│[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
        except PermissionError as e:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print(f"[red]│ ✗ Permission refusée : {e}{' ' * (38 - len(f'✗ Permission refusée : {e}'))}│[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")

    finally:
        db.close()

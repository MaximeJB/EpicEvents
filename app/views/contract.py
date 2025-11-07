"""Groupe composé de toutes les possibilités de contrat."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.auth import get_current_user
from app.managers.client import get_client
from app.managers.contract import (
    create_contract,
    get_contract,
    list_contracts,
    update_contract,
)
from app.db import SessionLocal

console = Console()


@click.group()
def contract():
    """Groupe composé de toutes les possibilités de contrat."""
    pass


@contract.command()
def create():
    """Créer un nouveau contrat.

    Returns:
        None: Affiche le résultat de la création dans la console.

    Raises:
        ValueError: Si le client n'existe pas ou données invalides.
        PermissionError: Si l'utilisateur n'a pas les permissions.
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
            client_id = click.prompt("Entrez l'ID du client", type=int)
            client = get_client(db, client_id)
            if not client:
                console.print("\n[red]╭───────────────────────────────────────╮[/red]")
                console.print("[red]│ ✗ Client non trouvé avec cet ID       │[/red]")
                console.print("[red]╰───────────────────────────────────────╯[/red]\n")
                return
            total_amount = click.prompt("Entrez le montant total du contrat", type=int)
            remaining_amount = click.prompt("Entrez le montant restant à honorer sur ce contrat", type=int)
            status_choice = click.prompt("Entrez le status du contrat : 's' pour signé, 'a' pour en attente")
            if status_choice == "s":
                status = "signed"
            elif status_choice == "a":
                status = "pending"
            else:
                console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
                console.print("[yellow]│ ⚠ Répondez soit 's' soit 'a'          │[/yellow]")
                console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
                return
            try:
                new_contract = create_contract(
                    db=db,
                    current_user=user,
                    client_id=client.id,
                    total_amount=total_amount,
                    remaining_amount=remaining_amount,
                    status=status,
                )
                console.print("\n[green]╭───────────────────────────────────────╮[/green]")
                console.print(
                    f"[green]│ ✓ Contrat créé : {new_contract.client.name} (ID: {new_contract.id}){' ' * (38 - len(f'✓ Contrat créé : {new_contract.client.name} (ID: {new_contract.id})'))}│[/green]"
                )
                console.print("[green]╰───────────────────────────────────────╯[/green]\n")
            except ValueError as e:
                console.print("\n[red]╭───────────────────────────────────────╮[/red]")
                console.print(f"[red]│ ✗ Erreur de valeur : {e}{' ' * (38 - len(f'✗ Erreur de valeur : {e}'))}│[/red]")
                console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            except PermissionError as e:
                console.print("\n[red]╭───────────────────────────────────────╮[/red]")
                console.print(
                    f"[red]│ ✗ Permission refusée : {e}{' ' * (38 - len(f'✗ Permission refusée : {e}'))}│[/red]"
                )
                console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    finally:
        db.close()


@contract.command()
@click.option('--unsigned', is_flag=True, help='Afficher uniquement les contrats non signés')
@click.option('--unpaid', is_flag=True, help='Afficher uniquement les contrats non entièrement payés')
def list(unsigned, unpaid):
    """Lister les contrats.

    Args:
        unsigned (bool): Si True, filtre les contrats non signés.
        unpaid (bool): Si True, filtre les contrats avec montant restant > 0.

    Returns:
        None: Affiche les contrats dans un tableau Rich.
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
            contracts = list_contracts(db, user)

            # Appliquer les filtres si demandés
            if unsigned:
                contracts = [c for c in contracts if c.status != "signed"]
            if unpaid:
                contracts = [c for c in contracts if c.remaining_amount > 0]

            if not contracts:
                console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
                console.print("[yellow]│ Aucun contrat à afficher               │[/yellow]")
                console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
                return
            else:
                table = Table(title="Liste des Contrats")
                table.add_column("ID", style="cyan", justify="center")
                table.add_column("Client", style="green")
                table.add_column("Date création", style="blue")
                table.add_column("Status", justify="center")
                table.add_column("Montant total", justify="right", style="yellow")
                table.add_column("Restant", justify="right", style="red")

                for contract in contracts:
                    status_display = (
                        "[green]✓ Signé[/green]" if contract.status == "signed" else "[red]✗ En attente[/red]"
                    )
                    table.add_row(
                        str(contract.id),
                        contract.client.name,
                        str(contract.created_at.strftime("%d/%m/%Y")),
                        status_display,
                        f"{contract.total_amount} €",
                        f"{contract.remaining_amount} €",
                    )

                console.print(table)
    finally:
        db.close()


@contract.command()
def update():
    """Mettre à jour un contrat.

    Returns:
        None: Affiche le résultat de la modification.

    Raises:
        ValueError: Si le contrat n'existe pas.
        PermissionError: Si l'utilisateur n'a pas les permissions.
    """
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if user is None:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Pas d'utilisateur connecté          │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        contract_id = click.prompt("Quel est l'ID du contrat à mettre à jour ?", type=int)

        target_contract = get_contract(db, contract_id)
        if not target_contract:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Aucun contrat trouvé avec cet ID    │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        panel = Panel(
            f"[bold]Client:[/bold] {target_contract.client.name}\n"
            f"[bold]Status:[/bold] {target_contract.status}\n"
            f"[bold]Montant total:[/bold] {target_contract.total_amount} €\n"
            f"[bold]Montant restant:[/bold] {target_contract.remaining_amount} €\n"
            f"[bold]Date création:[/bold] {target_contract.created_at.strftime('%d/%m/%Y')}",
            title="Contrat actuel",
            border_style="blue",
        )
        console.print(panel)
        console.print("[yellow]Laissez vide pour ne pas modifier un champ[/yellow]\n")

        total_amount = click.prompt("Nouveau montant total", default="", show_default=False)
        remaining_amount = click.prompt("Nouveau montant restant", default="", show_default=False)
        status = click.prompt("Nouveau status", default="", show_default=False)

        kwargs = {}
        if total_amount:
            kwargs['total_amount'] = int(total_amount)
        if remaining_amount:
            kwargs['remaining_amount'] = int(remaining_amount)
        if status:
            kwargs['status'] = status

        if not kwargs:
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ Aucune modification effectuée          │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
            return

        try:
            updated = update_contract(db, current_user=user, contract_id=contract_id, **kwargs)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(
                f"[green]│ ✓ Contrat mis à jour : {updated.client.name} - {updated.status} (ID: {updated.id}){' ' * (38 - len(f'✓ Contrat mis à jour : {updated.client.name} - {updated.status} (ID: {updated.id})'))}│[/green]"
            )
            console.print("[green]╰───────────────────────────────────────╯[/green]\n")
        except ValueError as e:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print(f"[red]│ ✗ Erreur : {e}{' ' * (38 - len(f'✗ Erreur : {e}'))}│[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
        except PermissionError as e:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print(f"[red]│ ✗ Permission refusée : {e}{' ' * (38 - len(f'✗ Permission refusée : {e}'))}│[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")

    finally:
        db.close()

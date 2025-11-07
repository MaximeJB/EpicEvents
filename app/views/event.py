"""Groupe composé de toutes les possibilités des événements."""

from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.auth import get_current_user
from app.managers.contract import get_contract
from app.managers.event import (
    assign_support,
    create_event,
    get_event,
    list_events,
    update_event,
)
from app.db import SessionLocal

console = Console()


@click.group()
def event():
    """Groupe composé de toutes les possibilités des événements."""
    pass


@event.command()
def create():
    """Créer un nouvel événement.

    Returns:
        None: Affiche le résultat de la création dans la console.

    Raises:
        ValueError: Si le contrat n'existe pas ou n'est pas signé.
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

        console.print("\n[bold magenta]═══════════════════════════════════[/bold magenta]")
        console.print("[bold magenta]    CRÉATION D'UN ÉVÉNEMENT[/bold magenta]")
        console.print("[bold magenta]═══════════════════════════════════[/bold magenta]\n")

        contract_id = click.prompt("ID du contrat", type=int)
        contract = get_contract(db, contract_id)
        if not contract:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Contrat non trouvé avec cet ID      │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        status_color = "[green]Signé[/green]" if contract.status == "signed" else "[red]Non signé[/red]"
        panel = Panel(
            f"[bold]Client:[/bold] {contract.client.name}\n"
            f"[bold]Status:[/bold] {status_color}\n"
            f"[bold]Montant total:[/bold] {contract.total_amount} €\n"
            f"[bold]Montant restant:[/bold] {contract.remaining_amount} €\n"
            f"[bold]Commercial:[/bold] {contract.client.sales_contact.name}",
            title="📋 Contrat sélectionné",
            border_style="cyan",
            padding=(1, 2),
        )
        console.print(panel)

        start_date_str = click.prompt("Date de début (JJ/MM/AAAA HH:MM ou JJ/MM/AAAA)")
        end_date_str = click.prompt("Date de fin (JJ/MM/AAAA HH:MM ou JJ/MM/AAAA)")
        location = click.prompt("Lieu de l'événement")
        attendees = click.prompt("Nombre de participants", type=int)

        date_formats = ["%d/%m/%Y %H:%M", "%d/%m/%Y"]
        start_date = None
        end_date = None

        for fmt in date_formats:
            try:
                start_date = datetime.strptime(start_date_str, fmt)
                break
            except ValueError:
                continue

        if not start_date:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Format de date début invalide.      │[/red]")
            console.print("[red]│   Utilisez JJ/MM/AAAA HH:MM ou        │[/red]")
            console.print("[red]│   JJ/MM/AAAA                           │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        for fmt in date_formats:
            try:
                end_date = datetime.strptime(end_date_str, fmt)
                break
            except ValueError:
                continue

        if not end_date:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Format de date fin invalide.        │[/red]")
            console.print("[red]│   Utilisez JJ/MM/AAAA HH:MM ou        │[/red]")
            console.print("[red]│   JJ/MM/AAAA                           │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        try:
            new_event = create_event(
                db=db,
                current_user=user,
                start_date=start_date,
                end_date=end_date,
                location=location,
                attendees=attendees,
                contract_id=contract_id,
            )
            panel = Panel(
                f"[green]Événement créé avec succès ![/green]\n\n"
                f"[bold]ID:[/bold] {new_event.id}\n"
                f"[bold]Client:[/bold] {new_event.contract.client.name}\n"
                f"[bold]Lieu:[/bold] {new_event.location}\n"
                f"[bold]Date:[/bold] {new_event.start_date.strftime('%d/%m/%Y %H:%M')} → {new_event.end_date.strftime('%d/%m/%Y %H:%M')}\n"
                f"[bold]Participants:[/bold] {new_event.attendees}",
                title="✓ Nouvel événement",
                border_style="green",
                padding=(1, 2),
            )
            console.print(panel)
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


@event.command()
@click.option('--no-support', is_flag=True, help='Afficher uniquement les événements sans support assigné')
@click.option('--mine', is_flag=True, help='Afficher uniquement les événements qui me sont assignés (support)')
def list(no_support, mine):
    """Lister les événements.

    Args:
        no_support (bool): Si True, filtre les événements sans support assigné.
        mine (bool): Si True, filtre les événements assignés à l'utilisateur connecté.

    Returns:
        None: Affiche les événements dans un tableau Rich.
    """
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if user is None:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Pas d'utilisateur connecté          │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        events = list_events(db, user)

        # Appliquer les filtres si demandés
        if no_support:
            events = [e for e in events if e.support_contact_id is None]
        if mine:
            events = [e for e in events if e.support_contact_id == user.id]

        if not events:
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ Aucun événement à afficher             │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
            return

        table = Table(title="Liste des Événements")
        table.add_column("ID", style="cyan", justify="center")
        table.add_column("Client", style="green")
        table.add_column("Lieu", style="yellow")
        table.add_column("Date début", style="blue")
        table.add_column("Participants", justify="center")
        table.add_column("Support", style="magenta")

        for evt in events:
            support_name = evt.support_contact.name if evt.support_contact else "[red]Non assigné[/red]"
            table.add_row(
                str(evt.id),
                evt.contract.client.name,
                evt.location,
                evt.start_date.strftime("%d/%m/%Y %H:%M"),
                str(evt.attendees),
                support_name,
            )

        console.print(table)
    finally:
        db.close()


@event.command()
def update():
    """Mettre à jour un événement.

    Returns:
        None: Affiche le résultat de la modification.

    Raises:
        ValueError: Si l'événement n'existe pas.
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

        event_id = click.prompt("Quel est l'ID de l'événement à mettre à jour ?", type=int)

        target_event = get_event(db, event_id)
        if not target_event:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Aucun événement trouvé avec cet ID  │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        support_info = target_event.support_contact.name if target_event.support_contact else "Non assigné"
        panel = Panel(
            f"[bold]Client:[/bold] {target_event.contract.client.name}\n"
            f"[bold]Lieu:[/bold] {target_event.location}\n"
            f"[bold]Date début:[/bold] {target_event.start_date.strftime('%d/%m/%Y %H:%M')}\n"
            f"[bold]Date fin:[/bold] {target_event.end_date.strftime('%d/%m/%Y %H:%M')}\n"
            f"[bold]Participants:[/bold] {target_event.attendees}\n"
            f"[bold]Support:[/bold] {support_info}\n"
            f"[bold]Notes:[/bold] {target_event.notes or 'Aucune'}",
            title="Événement actuel",
            border_style="blue",
        )
        console.print(panel)
        console.print("[yellow]Laissez vide pour ne pas modifier un champ[/yellow]\n")

        location = click.prompt("Nouveau lieu", default="", show_default=False)
        start_date_str = click.prompt(
            "Nouvelle date début (JJ/MM/AAAA HH:MM ou JJ/MM/AAAA)", default="", show_default=False
        )
        end_date_str = click.prompt(
            "Nouvelle date fin (JJ/MM/AAAA HH:MM ou JJ/MM/AAAA)", default="", show_default=False
        )
        attendees_str = click.prompt("Nouveau nombre de participants", default="", show_default=False)
        notes = click.prompt("Nouvelles notes", default="", show_default=False)

        kwargs = {}
        date_formats = ["%d/%m/%Y %H:%M", "%d/%m/%Y"]

        if location:
            kwargs['location'] = location

        if start_date_str:
            start_date_parsed = None
            for fmt in date_formats:
                try:
                    start_date_parsed = datetime.strptime(start_date_str, fmt)
                    break
                except ValueError:
                    continue
            if not start_date_parsed:
                console.print("\n[red]╭───────────────────────────────────────╮[/red]")
                console.print("[red]│ ✗ Format de date début invalide.      │[/red]")
                console.print("[red]│   Utilisez JJ/MM/AAAA HH:MM ou        │[/red]")
                console.print("[red]│   JJ/MM/AAAA                           │[/red]")
                console.print("[red]╰───────────────────────────────────────╯[/red]\n")
                return
            kwargs['start_date'] = start_date_parsed

        if end_date_str:
            end_date_parsed = None
            for fmt in date_formats:
                try:
                    end_date_parsed = datetime.strptime(end_date_str, fmt)
                    break
                except ValueError:
                    continue
            if not end_date_parsed:
                console.print("\n[red]╭───────────────────────────────────────╮[/red]")
                console.print("[red]│ ✗ Format de date fin invalide.        │[/red]")
                console.print("[red]│   Utilisez JJ/MM/AAAA HH:MM ou        │[/red]")
                console.print("[red]│   JJ/MM/AAAA                           │[/red]")
                console.print("[red]╰───────────────────────────────────────╯[/red]\n")
                return
            kwargs['end_date'] = end_date_parsed

        if attendees_str:
            kwargs['attendees'] = int(attendees_str)
        if notes:
            kwargs['notes'] = notes

        if not kwargs:
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ Aucune modification effectuée          │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
            return

        try:
            updated = update_event(db, current_user=user, event_id=event_id, **kwargs)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(
                f"[green]│ ✓ Événement mis à jour : {updated.contract.client.name} - {updated.location} (ID: {updated.id}){' ' * (38 - len(f'✓ Événement mis à jour : {updated.contract.client.name} - {updated.location} (ID: {updated.id})'))}│[/green]"
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


@event.command()
def assign():
    """Assigner un support à un événement.

    Returns:
        None: Affiche le résultat de l'assignation.

    Raises:
        ValueError: Si l'événement ou le support n'existe pas.
        PermissionError: Si l'utilisateur n'a pas les permissions (gestion uniquement).
    """
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if user is None:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Pas d'utilisateur connecté          │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        event_id = click.prompt("ID de l'événement", type=int)
        target_event = get_event(db, event_id)
        if not target_event:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Événement non trouvé                 │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        current_support = (
            target_event.support_contact.name if target_event.support_contact else "[red]Non assigné[/red]"
        )
        panel = Panel(
            f"[bold]Client:[/bold] {target_event.contract.client.name}\n"
            f"[bold]Lieu:[/bold] {target_event.location}\n"
            f"[bold]Date:[/bold] {target_event.start_date.strftime('%d/%m/%Y %H:%M')}\n"
            f"[bold]Support actuel:[/bold] {current_support}",
            title="🎯 Événement à assigner",
            border_style="yellow",
            padding=(1, 2),
        )
        console.print(panel)

        support_id = click.prompt("\nID du collaborateur support à assigner", type=int)

        try:
            updated_event = assign_support(db, current_user=user, event_id=event_id, support_user_id=support_id)
            panel = Panel(
                f"[green]Support assigné avec succès ![/green]\n\n"
                f"[bold]Événement:[/bold] {updated_event.contract.client.name}\n"
                f"[bold]Lieu:[/bold] {updated_event.location}\n"
                f"[bold]Support:[/bold] {updated_event.support_contact.name}",
                title="✓ Support assigné",
                border_style="green",
                padding=(1, 2),
            )
            console.print(panel)
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

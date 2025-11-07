"""Point d'entrée principal de l'application Epic Events CRM.

Ce module fournit un menu interactif qui permet de naviguer
dans toutes les fonctionnalités de l'application sans avoir à
mémoriser les commandes Click.
"""

import os
from datetime import datetime
from decimal import Decimal

import click
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from app.auth import get_current_user, login
from app.managers.client import create_client, get_client, list_clients, update_client
from app.managers.contract import (
    create_contract,
    get_contract,
    list_contracts,
    update_contract,
)
from app.managers.event import create_event, get_event, list_events, update_event
from app.managers.user import (
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
)
from app.db import SessionLocal
from app.models import Role

console = Console()


def clear_screen():
    """Affiche un séparateur visuel pour nettoyer l'écran."""
    console.print("\n" * 2)


def show_header():
    """Affiche l'en-tête de l'application avec ASCII art."""
    ascii_art = """
    ███████╗██████╗ ██╗ ██████╗    ███████╗██╗   ██╗███████╗███╗   ██╗████████╗███████╗
    ██╔════╝██╔══██╗██║██╔════╝    ██╔════╝██║   ██║██╔════╝████╗  ██║╚══██╔══╝██╔════╝
    █████╗  ██████╔╝██║██║         █████╗  ██║   ██║█████╗  ██╔██╗ ██║   ██║   ███████╗
    ██╔══╝  ██╔═══╝ ██║██║         ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║   ██║   ╚════██║
    ███████╗██║     ██║╚██████╗    ███████╗ ╚████╔╝ ███████╗██║ ╚████║   ██║   ███████║
    ╚══════╝╚═╝     ╚═╝ ╚═════╝    ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝
    """

    header = Panel(
        f"[bold cyan]{ascii_art}[/bold cyan]\n"
        + "[bold white]Customer Relationship Management System[/bold white]\n"
        + "[dim]v1.0 - Gestion professionnelle d'événements[/dim]",
        border_style="bright_cyan",
        box=box.DOUBLE,
        padding=(1, 2),
    )
    console.print(header)
    console.print()


def get_logged_user():
    """Retourne l'utilisateur connecté ou None.

    Returns:
        User or None: L'utilisateur connecté, ou None si non connecté.
    """
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if user:
            _ = user.role
        return user
    finally:
        db.close()


def require_authentication(func):
    """Décorateur pour vérifier qu'un utilisateur est connecté.

    Args:
        func: La fonction à décorer.

    Returns:
        La fonction décorée qui vérifie l'authentification.
    """

    def wrapper(*args, **kwargs):
        user = get_logged_user()
        if not user:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Vous devez être connecté            │[/red]")
            console.print("[red]│   Utilisez le menu Authentification   │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return
        return func(*args, **kwargs)

    return wrapper


def menu_auth():
    """Menu d'authentification."""
    while True:
        clear_screen()
        show_header()

        user = get_logged_user()
        if user:
            console.print(f"[green]✓ Connecté en tant que : {user.name} ({user.role.name})[/green]\n")
        else:
            console.print("[yellow]⚠ Non connecté[/yellow]\n")

        console.print("[bold cyan]🔐 AUTHENTIFICATION[/bold cyan]\n")
        console.print("1. Se connecter")
        console.print("2. Voir mon profil")
        console.print("3. Se déconnecter")
        console.print("0. Retour au menu principal\n")

        choice = Prompt.ask("Votre choix", choices=["0", "1", "2", "3"])

        if choice == "0":
            break
        elif choice == "1":
            action_login()
        elif choice == "2":
            action_whoami()
        elif choice == "3":
            action_logout()


def action_login():
    """Action : se connecter."""
    clear_screen()
    console.print("[bold cyan]🔐 CONNEXION[/bold cyan]\n")

    email = Prompt.ask("Email")
    password = Prompt.ask("Mot de passe", password=True)

    db = SessionLocal()
    try:
        success = login(db, email, password)
        if success:
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print("[green]│ ✓ Connexion réussie                   │[/green]")
            console.print("[green]╰───────────────────────────────────────╯[/green]\n")
        else:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Identifiants invalides              │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_whoami():
    """Action : afficher le profil de l'utilisateur connecté."""
    user = get_logged_user()
    if not user:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print("[red]│ ✗ Vous n'êtes pas connecté            │[/red]")
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    else:
        console.print("\n[cyan]📋 Profil utilisateur[/cyan]")
        console.print(f"  • Nom : {user.name}")
        console.print(f"  • Email : {user.email}")
        console.print(f"  • Département : {user.department}")
        console.print(f"  • Rôle : {user.role.name}")
        if hasattr(user, 'is_superuser') and user.is_superuser:
            console.print("  • [bold yellow]⭐ SUPERUSER[/bold yellow]")
        console.print()

    input("Appuyez sur Entrée pour continuer...")


def action_logout():
    """Action : se déconnecter."""
    if os.path.exists(".epicevents_token"):
        os.remove(".epicevents_token")
        console.print("\n[green]╭───────────────────────────────────────╮[/green]")
        console.print("[green]│ ✓ Déconnexion réussie                 │[/green]")
        console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    else:
        console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
        console.print("[yellow]│ ⚠ Vous n'étiez pas connecté           │[/yellow]")
        console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")

    input("Appuyez sur Entrée pour continuer...")


@require_authentication
def menu_clients():
    """Menu de gestion des clients."""
    while True:
        clear_screen()
        show_header()
        console.print("[bold cyan]👥 GESTION DES CLIENTS[/bold cyan]\n")
        console.print("1. Créer un client")
        console.print("2. Lister les clients")
        console.print("3. Modifier un client")
        console.print("0. Retour au menu principal\n")

        choice = Prompt.ask("Votre choix", choices=["0", "1", "2", "3"])

        if choice == "0":
            break
        elif choice == "1":
            action_create_client()
        elif choice == "2":
            action_list_clients()
        elif choice == "3":
            action_update_client()


def action_create_client():
    """Action : créer un client."""
    clear_screen()
    console.print("[bold cyan]👥 CRÉER UN CLIENT[/bold cyan]\n")

    name = Prompt.ask("Nom du client")
    email = Prompt.ask("Email")
    phone = Prompt.ask("Téléphone")
    company = Prompt.ask("Nom de l'entreprise")

    db = SessionLocal()
    try:
        user = get_current_user(db)
        client = create_client(db, user, name, phone, company, email)

        console.print("\n[green]╭───────────────────────────────────────╮[/green]")
        console.print(
            f"[green]│ ✓ Client créé : {client.name} (ID: {client.id}){' ' * (38 - len(f'✓ Client créé : {client.name} (ID: {client.id})'))}│[/green]"
        )
        console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print("[red]│ ✗ Permission refusée{' ' * (38 - len('✗ Permission refusée'))}│[/red]")
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_list_clients():
    """Action : lister les clients."""
    clear_screen()
    console.print("[bold cyan]👥 LISTE DES CLIENTS[/bold cyan]\n")

    db = SessionLocal()
    try:
        user = get_current_user(db)
        clients = list_clients(db, user)

        if not clients:
            console.print("[yellow]Aucun client trouvé.[/yellow]\n")
        else:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("ID", style="dim")
            table.add_column("Nom")
            table.add_column("Entreprise")
            table.add_column("Téléphone")
            table.add_column("Email")

            for client in clients:
                table.add_row(str(client.id), client.name, client.company_name, client.phone_number, client.email)

            console.print(table)
            console.print(f"\n[dim]Total : {len(clients)} client(s)[/dim]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_update_client():
    """Action : modifier un client."""
    clear_screen()
    console.print("[bold cyan]👥 MODIFIER UN CLIENT[/bold cyan]\n")

    client_id = IntPrompt.ask("ID du client à modifier")

    db = SessionLocal()
    try:
        client = get_client(db, client_id)
        if not client:
            console.print(f"\n[red]✗ Client ID {client_id} introuvable[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        console.print(f"\n[cyan]Client actuel : {client.name}[/cyan]")
        console.print("[dim]Laissez vide pour ne pas modifier[/dim]\n")

        new_name = Prompt.ask("Nouveau nom", default="")
        new_phone = Prompt.ask("Nouveau téléphone", default="")
        new_company = Prompt.ask("Nouvelle entreprise", default="")
        new_email = Prompt.ask("Nouvel email", default="")

        kwargs = {}
        if new_name:
            kwargs["name"] = new_name
        if new_phone:
            kwargs["phone_number"] = new_phone
        if new_company:
            kwargs["company_name"] = new_company
        if new_email:
            kwargs["email"] = new_email

        if not kwargs:
            console.print("\n[yellow]Aucune modification effectuée.[/yellow]\n")
        else:
            user = get_current_user(db)
            updated = update_client(db, user, client_id, **kwargs)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(
                f"[green]│ ✓ Client {updated.name} mis à jour{' ' * (38 - len(f'✓ Client {updated.name} mis à jour'))}│[/green]"
            )
            console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(f"[red]│ ✗ Permission refusée{' ' * (38 - len('✗ Permission refusée'))}│[/red]")
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


@require_authentication
def menu_contrats():
    """Menu de gestion des contrats."""
    while True:
        clear_screen()
        show_header()
        console.print("[bold magenta]📄 GESTION DES CONTRATS[/bold magenta]\n")
        console.print("1. Créer un contrat")
        console.print("2. Lister les contrats")
        console.print("3. Modifier un contrat")
        console.print("4. Signer un contrat")
        console.print("0. Retour au menu principal\n")

        choice = Prompt.ask("Votre choix", choices=["0", "1", "2", "3", "4"])

        if choice == "0":
            break
        elif choice == "1":
            action_create_contract()
        elif choice == "2":
            action_list_contracts()
        elif choice == "3":
            action_update_contract()
        elif choice == "4":
            action_sign_contract()


def action_create_contract():
    """Action : créer un contrat."""
    clear_screen()
    console.print("[bold magenta]📄 CRÉER UN CONTRAT[/bold magenta]\n")

    client_id = IntPrompt.ask("ID du client")
    total_amount = Prompt.ask("Montant total")
    remaining_amount = Prompt.ask("Montant restant")

    db = SessionLocal()
    try:
        user = get_current_user(db)
        contract = create_contract(db, user, "pending", Decimal(total_amount), Decimal(remaining_amount), client_id)

        console.print("\n[green]╭───────────────────────────────────────╮[/green]")
        console.print(
            f"[green]│ ✓ Contrat créé (ID: {contract.id}){' ' * (38 - len(f'✓ Contrat créé (ID: {contract.id})'))}│[/green]"
        )
        console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(
            f"[red]│ ✗ Permission refusée (gestion seul){' ' * (38 - len('✗ Permission refusée (gestion seul)'))}│[/red]"
        )
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except ValueError as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_list_contracts():
    """Action : lister les contrats."""
    clear_screen()
    console.print("[bold magenta]📄 LISTE DES CONTRATS[/bold magenta]\n")

    db = SessionLocal()
    try:
        user = get_current_user(db)
        contracts = list_contracts(db, user)

        if not contracts:
            console.print("[yellow]Aucun contrat trouvé.[/yellow]\n")
        else:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Client")
            table.add_column("Montant total")
            table.add_column("Restant")
            table.add_column("Statut")
            table.add_column("Date")

            for contract in contracts:
                _ = contract.client
                table.add_row(
                    str(contract.id),
                    contract.client.name,
                    f"{contract.total_amount} €",
                    f"{contract.remaining_amount} €",
                    "✓ Signé" if contract.status == "signed" else "⏳ En attente",
                    contract.created_at.strftime("%d/%m/%Y"),
                )

            console.print(table)
            console.print(f"\n[dim]Total : {len(contracts)} contrat(s)[/dim]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_update_contract():
    """Action : modifier un contrat."""
    clear_screen()
    console.print("[bold magenta]📄 MODIFIER UN CONTRAT[/bold magenta]\n")

    contract_id = IntPrompt.ask("ID du contrat à modifier")

    db = SessionLocal()
    try:
        contract = get_contract(db, contract_id)
        if not contract:
            console.print(f"\n[red]✗ Contrat ID {contract_id} introuvable[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        console.print(f"\n[magenta]Contrat actuel : ID {contract.id}[/magenta]")
        console.print("[dim]Laissez vide pour ne pas modifier[/dim]\n")

        new_total = Prompt.ask("Nouveau montant total", default="")
        new_remaining = Prompt.ask("Nouveau montant restant", default="")
        new_status = Prompt.ask("Nouveau statut (pending/signed)", default="")

        kwargs = {}
        if new_total:
            kwargs["total_amount"] = Decimal(new_total)
        if new_remaining:
            kwargs["remaining_amount"] = Decimal(new_remaining)
        if new_status:
            if new_status not in ["pending", "signed"]:
                console.print("\n[red]✗ Statut invalide (pending ou signed uniquement)[/red]\n")
                input("Appuyez sur Entrée pour continuer...")
                return
            kwargs["status"] = new_status

        if not kwargs:
            console.print("\n[yellow]Aucune modification effectuée.[/yellow]\n")
        else:
            user = get_current_user(db)
            updated = update_contract(db, user, contract_id, **kwargs)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(
                f"[green]│ ✓ Contrat {updated.id} mis à jour{' ' * (38 - len(f'✓ Contrat {updated.id} mis à jour'))}│[/green]"
            )
            console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(f"[red]│ ✗ Permission refusée{' ' * (38 - len('✗ Permission refusée'))}│[/red]")
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_sign_contract():
    """Action : signer un contrat (changer statut à signed)."""
    clear_screen()
    console.print("[bold magenta]📄 SIGNER UN CONTRAT[/bold magenta]\n")

    contract_id = IntPrompt.ask("ID du contrat à signer")

    db = SessionLocal()
    try:
        contract = get_contract(db, contract_id)
        if not contract:
            console.print(f"\n[red]✗ Contrat ID {contract_id} introuvable[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        if contract.status == "signed":
            console.print("\n[yellow]⚠ Ce contrat est déjà signé[/yellow]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        user = get_current_user(db)
        updated = update_contract(db, user, contract_id, status="signed")
        console.print("\n[green]╭───────────────────────────────────────╮[/green]")
        console.print(
            f"[green]│ ✓ Contrat {updated.id} signé avec succès{' ' * (38 - len(f'✓ Contrat {updated.id} signé avec succès'))}│[/green]"
        )
        console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(f"[red]│ ✗ Permission refusée{' ' * (38 - len('✗ Permission refusée'))}│[/red]")
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


@require_authentication
def menu_events():
    """Menu de gestion des événements."""
    while True:
        clear_screen()
        show_header()
        console.print("[bold yellow]🎉 GESTION DES ÉVÉNEMENTS[/bold yellow]\n")
        console.print("1. Créer un événement")
        console.print("2. Lister les événements")
        console.print("3. Modifier un événement")
        console.print("4. Assigner un support")
        console.print("0. Retour au menu principal\n")

        choice = Prompt.ask("Votre choix", choices=["0", "1", "2", "3", "4"])

        if choice == "0":
            break
        elif choice == "1":
            action_create_event()
        elif choice == "2":
            action_list_events()
        elif choice == "3":
            action_update_event()
        elif choice == "4":
            action_assign_support()


def action_create_event():
    """Action : créer un événement."""
    clear_screen()
    console.print("[bold yellow]🎉 CRÉER UN ÉVÉNEMENT[/bold yellow]\n")

    contract_id = IntPrompt.ask("ID du contrat (doit être signé)")

    console.print("\n[dim]Format date : JJ/MM/AAAA HH:MM ou JJ/MM/AAAA[/dim]")
    start_date_str = Prompt.ask("Date de début")
    end_date_str = Prompt.ask("Date de fin")

    location = Prompt.ask("Lieu")
    attendees = IntPrompt.ask("Nombre de participants")
    notes = Prompt.ask("Notes", default="")

    db = SessionLocal()
    try:
        try:
            if ":" in start_date_str:
                start_date = datetime.strptime(start_date_str, "%d/%m/%Y %H:%M")
            else:
                start_date = datetime.strptime(start_date_str, "%d/%m/%Y")

            if ":" in end_date_str:
                end_date = datetime.strptime(end_date_str, "%d/%m/%Y %H:%M")
            else:
                end_date = datetime.strptime(end_date_str, "%d/%m/%Y")
        except ValueError:
            console.print("\n[red]✗ Format de date invalide[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        user = get_current_user(db)
        event = create_event(db, user, start_date, end_date, location, attendees, contract_id, notes)

        console.print("\n[green]╭───────────────────────────────────────╮[/green]")
        console.print(
            f"[green]│ ✓ Événement créé (ID: {event.id}){' ' * (38 - len(f'✓ Événement créé (ID: {event.id})'))}│[/green]"
        )
        console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(f"[red]│ ✗ Permission refusée{' ' * (38 - len('✗ Permission refusée'))}│[/red]")
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except ValueError as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_list_events():
    """Action : lister les événements."""
    clear_screen()
    console.print("[bold yellow]🎉 LISTE DES ÉVÉNEMENTS[/bold yellow]\n")

    db = SessionLocal()
    try:
        user = get_current_user(db)
        events = list_events(db, user)

        if not events:
            console.print("[yellow]Aucun événement trouvé.[/yellow]\n")
        else:
            table = Table(show_header=True, header_style="bold yellow")
            table.add_column("ID", style="dim")
            table.add_column("Client")
            table.add_column("Date début")
            table.add_column("Lieu")
            table.add_column("Participants")
            table.add_column("Support")

            for event in events:
                _ = event.contract.client
                support_name = event.support_contact.name if event.support_contact else "Non assigné"

                table.add_row(
                    str(event.id),
                    event.contract.client.name,
                    event.start_date.strftime("%d/%m/%Y %H:%M"),
                    event.location,
                    str(event.attendees),
                    support_name,
                )

            console.print(table)
            console.print(f"\n[dim]Total : {len(events)} événement(s)[/dim]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_update_event():
    """Action : modifier un événement."""
    clear_screen()
    console.print("[bold yellow]🎉 MODIFIER UN ÉVÉNEMENT[/bold yellow]\n")

    event_id = IntPrompt.ask("ID de l'événement à modifier")

    db = SessionLocal()
    try:
        event = get_event(db, event_id)
        if not event:
            console.print(f"\n[red]✗ Événement ID {event_id} introuvable[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        console.print(f"\n[yellow]Événement actuel : ID {event.id}[/yellow]")
        console.print("[dim]Laissez vide pour ne pas modifier[/dim]\n")

        new_location = Prompt.ask("Nouveau lieu", default="")
        new_attendees = Prompt.ask("Nouveau nombre de participants", default="")
        new_notes = Prompt.ask("Nouvelles notes", default="")

        kwargs = {}
        if new_location:
            kwargs["location"] = new_location
        if new_attendees:
            kwargs["attendees"] = int(new_attendees)
        if new_notes:
            kwargs["notes"] = new_notes

        if not kwargs:
            console.print("\n[yellow]Aucune modification effectuée.[/yellow]\n")
        else:
            user = get_current_user(db)
            updated = update_event(db, user, event_id, **kwargs)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(
                f"[green]│ ✓ Événement {updated.id} mis à jour{' ' * (38 - len(f'✓ Événement {updated.id} mis à jour'))}│[/green]"
            )
            console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(f"[red]│ ✗ Permission refusée{' ' * (38 - len('✗ Permission refusée'))}│[/red]")
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_assign_support():
    """Action : assigner un support à un événement."""
    clear_screen()
    console.print("[bold yellow]🎉 ASSIGNER UN SUPPORT[/bold yellow]\n")

    event_id = IntPrompt.ask("ID de l'événement")
    support_id = IntPrompt.ask("ID du collaborateur support")

    db = SessionLocal()
    try:
        user = get_current_user(db)
        update_event(db, user, event_id, support_contact_id=support_id)
        console.print("\n[green]╭───────────────────────────────────────╮[/green]")
        console.print(
            f"[green]│ ✓ Support assigné à l'événement{' ' * (38 - len('✓ Support assigné à l\'événement'))}│[/green]"
        )
        console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(
            f"[red]│ ✗ Permission refusée (gestion seul){' ' * (38 - len('✗ Permission refusée (gestion seul)'))}│[/red]"
        )
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


@require_authentication
def menu_collaborateurs():
    """Menu de gestion des collaborateurs (gestion uniquement)."""
    while True:
        clear_screen()
        show_header()
        console.print("[bold green]👤 GESTION DES COLLABORATEURS[/bold green]\n")
        console.print("1. Créer un collaborateur")
        console.print("2. Lister les collaborateurs")
        console.print("3. Modifier un collaborateur")
        console.print("4. Supprimer un collaborateur")
        console.print("0. Retour au menu principal\n")

        choice = Prompt.ask("Votre choix", choices=["0", "1", "2", "3", "4"])

        if choice == "0":
            break
        elif choice == "1":
            action_create_user()
        elif choice == "2":
            action_list_users()
        elif choice == "3":
            action_update_user()
        elif choice == "4":
            action_delete_user()


def action_create_user():
    """Action : créer un collaborateur."""
    clear_screen()
    console.print("[bold green]👤 CRÉER UN COLLABORATEUR[/bold green]\n")

    name = Prompt.ask("Nom")
    email = Prompt.ask("Email")
    password = Prompt.ask("Mot de passe", password=True)
    department = Prompt.ask("Département")
    role_name = Prompt.ask("Rôle (sales/support/gestion)")

    if role_name not in ["sales", "support", "gestion"]:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(f"[red]│ ✗ Rôle invalide{' ' * (38 - len('✗ Rôle invalide'))}│[/red]")
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
        input("Appuyez sur Entrée pour continuer...")
        return

    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            console.print(f"\n[red]✗ Rôle {role_name} introuvable dans la base[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        user = get_current_user(db)
        new_user = create_user(db, user, email, password, name, department, role.id)

        console.print("\n[green]╭───────────────────────────────────────╮[/green]")
        console.print(
            f"[green]│ ✓ Collaborateur créé : {new_user.name}{' ' * (38 - len(f'✓ Collaborateur créé : {new_user.name}'))}│[/green]"
        )
        console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(
            f"[red]│ ✗ Permission refusée (gestion seul){' ' * (38 - len('✗ Permission refusée (gestion seul)'))}│[/red]"
        )
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_list_users():
    """Action : lister les collaborateurs."""
    clear_screen()
    console.print("[bold green]👤 LISTE DES COLLABORATEURS[/bold green]\n")

    db = SessionLocal()
    try:
        user = get_current_user(db)
        users = list_users(db, user)

        table = Table(show_header=True, header_style="bold green")
        table.add_column("ID", style="dim")
        table.add_column("Nom")
        table.add_column("Email")
        table.add_column("Département")
        table.add_column("Rôle")

        for u in users:
            _ = u.role
            table.add_row(str(u.id), u.name, u.email, u.department or "N/A", u.role.name)

        console.print(table)
        console.print(f"\n[dim]Total : {len(users)} collaborateur(s)[/dim]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(
            f"[red]│ ✗ Permission refusée (gestion seul){' ' * (38 - len('✗ Permission refusée (gestion seul)'))}│[/red]"
        )
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_update_user():
    """Action : modifier un collaborateur."""
    clear_screen()
    console.print("[bold green]👤 MODIFIER UN COLLABORATEUR[/bold green]\n")

    user_id = IntPrompt.ask("ID du collaborateur à modifier")

    db = SessionLocal()
    try:
        target_user = get_user_by_id(db, user_id)
        if not target_user:
            console.print(f"\n[red]✗ Collaborateur ID {user_id} introuvable[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        console.print(f"\n[green]Collaborateur actuel : {target_user.name}[/green]")
        console.print("[dim]Laissez vide pour ne pas modifier[/dim]\n")

        new_name = Prompt.ask("Nouveau nom", default="")
        new_department = Prompt.ask("Nouveau département", default="")
        new_role = Prompt.ask("Nouveau rôle (sales/support/gestion)", default="")

        kwargs = {}
        if new_name:
            kwargs["name"] = new_name
        if new_department:
            kwargs["department"] = new_department
        if new_role:
            if new_role not in ["sales", "support", "gestion"]:
                console.print("\n[red]✗ Rôle invalide[/red]\n")
                input("Appuyez sur Entrée pour continuer...")
                return
            role = db.query(Role).filter(Role.name == new_role).first()
            if role:
                kwargs["role_id"] = role.id

        if not kwargs:
            console.print("\n[yellow]Aucune modification effectuée.[/yellow]\n")
        else:
            user = get_current_user(db)
            updated = update_user(db, user, user_id, **kwargs)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(
                f"[green]│ ✓ Collaborateur {updated.name} mis à jour{' ' * (38 - len(f'✓ Collaborateur {updated.name} mis à jour'))}│[/green]"
            )
            console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(
            f"[red]│ ✗ Permission refusée (gestion seul){' ' * (38 - len('✗ Permission refusée (gestion seul)'))}│[/red]"
        )
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


def action_delete_user():
    """Action : supprimer un collaborateur."""
    clear_screen()
    console.print("[bold green]👤 SUPPRIMER UN COLLABORATEUR[/bold green]\n")

    user_id = IntPrompt.ask("ID du collaborateur à supprimer")

    db = SessionLocal()
    try:
        target_user = get_user_by_id(db, user_id)
        if not target_user:
            console.print(f"\n[red]✗ Collaborateur ID {user_id} introuvable[/red]\n")
            input("Appuyez sur Entrée pour continuer...")
            return

        console.print(
            f"\n[yellow]⚠ Vous êtes sur le point de supprimer : {target_user.name} ({target_user.email})[/yellow]"
        )
        confirm = Confirm.ask("Êtes-vous sûr ?")

        if not confirm:
            console.print("\n[yellow]Suppression annulée.[/yellow]\n")
        else:
            user = get_current_user(db)
            delete_user(db, user, user_id)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(f"[green]│ ✓ Collaborateur supprimé{' ' * (38 - len('✓ Collaborateur supprimé'))}│[/green]")
            console.print("[green]╰───────────────────────────────────────╯[/green]\n")
    except PermissionError:
        console.print("\n[red]╭───────────────────────────────────────╮[/red]")
        console.print(
            f"[red]│ ✗ Permission refusée (gestion seul){' ' * (38 - len('✗ Permission refusée (gestion seul)'))}│[/red]"
        )
        console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    except Exception as e:
        console.print(f"\n[red]✗ Erreur : {e}[/red]\n")
    finally:
        db.close()

    input("Appuyez sur Entrée pour continuer...")


@click.command(name="run")
def menu_principal():
    """Menu principal de l'application avec design amélioré."""
    while True:
        clear_screen()
        show_header()

        user = get_logged_user()
        if user:
            status_text = (
                "[bold green]✓ CONNECTÉ[/bold green]\n\n"
                f"[white]Utilisateur : [/white][cyan]{user.name}[/cyan]\n"
                f"[white]Rôle : [/white][yellow]{user.role.name.upper()}[/yellow]"
            )
            if hasattr(user, 'is_superuser') and user.is_superuser:
                status_text += "\n[bold yellow]⭐ SUPERUSER[/bold yellow]"
            status_style = "green"
        else:
            status_text = "[bold yellow]⚠ NON CONNECTÉ[/bold yellow]\n\n[dim]Utilisez le menu Authentification[/dim]"
            status_style = "yellow"

        status_panel = Panel(
            status_text, title="[bold]Statut[/bold]", border_style=status_style, box=box.ROUNDED, width=40
        )
        console.print(status_panel)
        console.print()

        menu_title = Panel("[bold white]MENU PRINCIPAL[/bold white]", border_style="bright_cyan", box=box.DOUBLE)
        console.print(menu_title)
        console.print()

        option_1 = Panel(
            "[bold cyan]1. 🔐 Authentification[/bold cyan]\n[dim]Connexion / Profil / Déconnexion[/dim]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        option_2 = Panel(
            "[bold blue]2. 👥 Clients[/bold blue]\n[dim]Créer, lister, modifier[/dim]",
            border_style="blue",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        option_3 = Panel(
            "[bold magenta]3. 📄 Contrats[/bold magenta]\n[dim]Gérer les contrats clients[/dim]",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        option_4 = Panel(
            "[bold yellow]4. 🎉 Événements[/bold yellow]\n[dim]Planifier et organiser[/dim]",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        option_5 = Panel(
            "[bold green]5. 👤 Collaborateurs[/bold green]\n[dim]Gestion des utilisateurs[/dim]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 1),
        )
        option_0 = Panel(
            "[bold red]0. ❌ Quitter[/bold red]\n[dim]Fermer l'application[/dim]",
            border_style="red",
            box=box.ROUNDED,
            padding=(0, 1),
        )

        columns_1 = Columns([option_1, option_2], equal=True, expand=True, padding=(0, 2))
        columns_2 = Columns([option_3, option_4], equal=True, expand=True, padding=(0, 2))
        columns_3 = Columns([option_5, option_0], equal=True, expand=True, padding=(0, 2))

        console.print(columns_1)
        console.print(columns_2)
        console.print(columns_3)

        choice_panel = Panel(
            "Entrez le [bold cyan]numéro[/bold cyan] de votre choix : [bold]1[/bold], [bold]2[/bold], [bold]3[/bold], [bold]4[/bold], [bold]5[/bold] ou [bold red]0[/bold red]",
            border_style="bright_black",
            box=box.SIMPLE,
        )
        console.print(choice_panel)

        choice = Prompt.ask("›", choices=["0", "1", "2", "3", "4", "5"])

        if choice == "0":
            goodbye = Panel(
                "[bold cyan]Merci d'avoir utilisé Epic Events CRM[/bold cyan]\n\n[white]À bientôt ! 👋[/white]",
                border_style="cyan",
                box=box.DOUBLE,
                padding=(1, 2),
            )
            console.print()
            console.print(goodbye)
            console.print()
            break
        elif choice == "1":
            menu_auth()
        elif choice == "2":
            menu_clients()
        elif choice == "3":
            menu_contrats()
        elif choice == "4":
            menu_events()
        elif choice == "5":
            menu_collaborateurs()


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interruption par l'utilisateur. Au revoir ![/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Erreur critique : {e}[/red]\n")

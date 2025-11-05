"""Groupe composé de toutes les possibilités des collaborateurs."""
from getpass import getpass

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.auth import get_current_user
from app.crud.crud_user import (
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    update_user,
)
from app.db import SessionLocal
from app.models import Role

console = Console()


@click.group()
def collab():
    """Groupe composé de toutes les possibilités des collaborateurs."""
    pass


@collab.command()
def create():
    """Créer un nouveau collaborateur.

    Returns:
        None: Affiche le résultat de la création dans la console.

    Raises:
        ValueError: Si le rôle est invalide ou données incorrectes.
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

        console.print("\n[bold cyan]═══════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]  CRÉATION D'UN COLLABORATEUR[/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════[/bold cyan]\n")

        name = click.prompt("Nom du collaborateur")
        email = click.prompt("Email")
        password = getpass("Mot de passe temporaire : ")
        department = click.prompt("Département (sales/support/gestion)")

        role = db.query(Role).filter(Role.name == department).first()
        if not role:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Rôle invalide. Utilisez : sales,    │[/red]")
            console.print("[red]│   support ou gestion                   │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        try:
            new_collab = create_user(db=db, current_user=user,
                                     name=name,
                                     email=email,
                                     password=password,
                                     department=department,
                                     role_id=role.id)
            panel = Panel(
                f"[green]Collaborateur créé avec succès ![/green]\n\n"
                f"[bold]Nom:[/bold] {new_collab.name}\n"
                f"[bold]Email:[/bold] {new_collab.email}\n"
                f"[bold]Rôle:[/bold] {new_collab.role.name}\n"
                f"[bold]Département:[/bold] {new_collab.department}",
                title="✓ Nouveau collaborateur",
                border_style="green",
                padding=(1, 2)
            )
            console.print(panel)
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


@collab.command()
def list():
    """Lister les collaborateurs.

    Returns:
        None: Affiche les collaborateurs dans un tableau Rich.
    """
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if user is None:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Pas d'utilisateur connecté          │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        collabs = list_users(db, user)
        if not collabs:
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ Aucun collaborateur à afficher         │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
            return

        table = Table(title="Liste des Collaborateurs")
        table.add_column("ID", style="cyan", justify="center")
        table.add_column("Nom", style="green")
        table.add_column("Email", style="blue")
        table.add_column("Département", justify="center", style="yellow")
        table.add_column("Rôle", justify="center", style="magenta")

        for collab in collabs:
            table.add_row(
                str(collab.id),
                collab.name,
                collab.email,
                collab.department,
                collab.role.name
            )

        console.print(table)
    finally:
        db.close()


@collab.command()
def update():
    """Mettre à jour un collaborateur.

    Returns:
        None: Affiche le résultat de la modification.

    Raises:
        ValueError: Si le collaborateur ou le rôle n'existe pas.
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

        collab_id = click.prompt("Quel est l'ID du collaborateur à mettre à jour ?", type=int)

        target_collab = get_user_by_id(db, collab_id)
        if not target_collab:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Aucun collaborateur trouvé avec cet │[/red]")
            console.print("[red]│   ID                                   │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        panel = Panel(
            f"[bold]Nom:[/bold] {target_collab.name}\n"
            f"[bold]Email:[/bold] {target_collab.email}\n"
            f"[bold]Département:[/bold] {target_collab.department}\n"
            f"[bold]Rôle:[/bold] {target_collab.role.name}",
            title="Collaborateur actuel",
            border_style="blue"
        )
        console.print(panel)
        console.print("[yellow]Laissez vide pour ne pas modifier un champ[/yellow]\n")

        name = click.prompt("Nouveau nom", default="", show_default=False)
        email = click.prompt("Nouvel email", default="", show_default=False)
        department = click.prompt("Nouveau département", default="", show_default=False)
        role_name = click.prompt("Nouveau rôle (sales/support/gestion)", default="", show_default=False)

        kwargs = {}
        if name:
            kwargs['name'] = name
        if email:
            kwargs['email'] = email
        if department:
            kwargs['department'] = department
        if role_name:
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                console.print("\n[red]╭───────────────────────────────────────╮[/red]")
                console.print("[red]│ ✗ Rôle invalide                        │[/red]")
                console.print("[red]╰───────────────────────────────────────╯[/red]\n")
                return
            kwargs['role_id'] = role.id

        if not kwargs:
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ Aucune modification effectuée          │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
            return

        try:
            updated = update_user(db, current_user=user, user_id=collab_id, **kwargs)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(f"[green]│ ✓ Collaborateur mis à jour : {updated.name} - {updated.role.name} (ID: {updated.id}){' ' * (38 - len(f'✓ Collaborateur mis à jour : {updated.name} - {updated.role.name} (ID: {updated.id})'))}│[/green]")
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


@collab.command()
def delete():
    """Supprimer un collaborateur.

    Returns:
        None: Affiche le résultat de la suppression.

    Raises:
        ValueError: Si le collaborateur n'existe pas.
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

        collab_id = click.prompt("Quel est l'ID du collaborateur à supprimer ?", type=int)

        target_collab = get_user_by_id(db, collab_id)
        if not target_collab:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Aucun collaborateur trouvé avec cet │[/red]")
            console.print("[red]│   ID                                   │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
            return

        panel = Panel(
            f"[bold red]ATTENTION : Suppression définitive ![/bold red]\n\n"
            f"[bold]Nom:[/bold] {target_collab.name}\n"
            f"[bold]Email:[/bold] {target_collab.email}\n"
            f"[bold]Rôle:[/bold] {target_collab.role.name}",
            title="⚠ Collaborateur à supprimer",
            border_style="red"
        )
        console.print(panel)

        confirmation = click.prompt("Êtes-vous sûr ? (o/n)", type=str)
        if confirmation.lower() != 'o':
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ Suppression annulée                    │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
            return

        try:
            delete_user(db, current_user=user, user_id=collab_id)
            console.print("\n[green]╭───────────────────────────────────────╮[/green]")
            console.print(f"[green]│ ✓ Collaborateur {target_collab.name} supprimé{' ' * (38 - len(f'✓ Collaborateur {target_collab.name} supprimé'))}│[/green]")
            console.print(f"[green]│   avec succès{' ' * (38 - len('  avec succès'))}│[/green]")
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

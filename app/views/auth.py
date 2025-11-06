"""Commandes CLI pour l'authentification."""

import os
from getpass import getpass

import click
from rich.console import Console
from rich.panel import Panel

from app.auth import login as auth_login, get_current_user
from app.db import SessionLocal

console = Console()


@click.group()
def auth():
    """Groupe composé de toutes les possibilités de auth."""
    pass


@auth.command()
def login():
    """Authentifie un utilisateur et crée un token JWT."""
    console.print("\n[bold blue]═══════════════════════════════════[/bold blue]")
    console.print("[bold blue]    EPIC EVENTS - CONNEXION[/bold blue]")
    console.print("[bold blue]═══════════════════════════════════[/bold blue]\n")

    email = click.prompt('Email')
    password = getpass("Mot de passe : ")

    db = SessionLocal()
    try:
        if auth_login(db, email, password):
            user = get_current_user(db)
            panel = Panel(
                f"[green]Bienvenue {user.name} ![/green]\n\n"
                f"[bold]Email:[/bold] {user.email}\n"
                f"[bold]Rôle:[/bold] {user.role.name}\n"
                f"[bold]Département:[/bold] {user.department}",
                title="✓ Connexion réussie",
                border_style="green",
                padding=(1, 2),
            )
            console.print(panel)
        else:
            console.print("\n[red]╭───────────────────────────────────────╮[/red]")
            console.print("[red]│ ✗ Identifiants invalides              │[/red]")
            console.print("[red]╰───────────────────────────────────────╯[/red]\n")
    finally:
        db.close()


@auth.command()
def logout():
    """Déconnecte l'utilisateur actuellement connecté."""
    db = SessionLocal()
    try:
        user = get_current_user(db)

        if user and os.path.exists(".epicevents_token"):
            panel = Panel(
                f"[yellow]{user.name}[/yellow], vous avez été déconnecté avec succès.\n\n"
                f"À bientôt sur Epic Events !",
                title="✓ Déconnexion",
                border_style="green",
                padding=(1, 2),
            )
            os.remove(".epicevents_token")
            console.print(panel)
        else:
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ ⚠ Aucun utilisateur connecté          │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
    finally:
        db.close()


@auth.command()
def whoami():
    """Affiche l'utilisateur actuellement connecté."""
    db = SessionLocal()

    try:
        user = get_current_user(db)

        if user is None:
            console.print("\n[yellow]╭───────────────────────────────────────╮[/yellow]")
            console.print("[yellow]│ ⚠ Aucun utilisateur connecté          │[/yellow]")
            console.print("[yellow]╰───────────────────────────────────────╯[/yellow]\n")
        else:
            panel = Panel(
                f"[bold cyan]Nom:[/bold cyan] {user.name}\n"
                f"[bold cyan]Email:[/bold cyan] {user.email}\n"
                f"[bold cyan]Rôle:[/bold cyan] [green]{user.role.name}[/green]\n"
                f"[bold cyan]Département:[/bold cyan] {user.department}",
                title="👤 Profil utilisateur",
                border_style="blue",
                padding=(1, 2),
            )
            console.print(panel)
    finally:
        db.close()

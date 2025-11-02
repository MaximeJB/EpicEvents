import click
from getpass import getpass
from app.db import SessionLocal
from app.auth import login as auth_login

@click.group()
def auth():
    """Groupe composé de toutes les possibilités de auth"""
    pass

@auth.command()
def login():
    """Authentifie un utilisateur et crée un token JWT."""
    email = click.prompt('Entrez votre email : ')
    password = getpass("Votre mot de passe : ")

    db = SessionLocal()
    try:
        if auth_login(db, email, password):
            click.echo("✓ Connexion réussie")
        else:
            click.echo("✗ Identifiants invalides")
    finally:
        db.close()

@auth.command()
def logout():
    #a coder
    pass

@auth.command()
def whoami():
    #a code
    
    pass
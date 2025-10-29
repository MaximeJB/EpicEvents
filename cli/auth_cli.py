import click
from getpass import getpass
from app.crud.crud_user import login
from app.db import get_db_session

@click.command()
def login():
    email = click.prompt('Email')
    password = getpass("Password : ")

    db = get_db_session()
    login_user = login(db)

    if login_user(email, password):
        click.echo("Connexion réussie")
    else: 
        click.echo("Identifiant invalides")
"""
Premier programme CLI avec Click.
Ce fichier sert à apprendre les bases de Click.
"""
import click

@click.group()
def main():
    """Groupe composé de hello et de bye --name"""
    pass

@main.command()
@click.option('--name', default = "utilisateur", help="Nom de la personne à saluer.")
def hello(name):
    """Affiche un message de bienvenue."""
    click.echo(f"Bonjour ! {name}")

@main.command()
@click.option('--name', default = "utilisateur", help="Nom de la personne à saluer.")
def bye(name):
    """Affiche un message d'au revoir."""
    click.echo(f"Bye ! {name}")


if __name__ == "__main__":
    main()

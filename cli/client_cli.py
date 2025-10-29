import click 
from app.models import Client

@client.command()
def create():
    """
    Créer un nouveau client.
    
    Flow:
        1. Vérifier que l'utilisateur est connecté
        2. Demander les infos du client
        3. Appeler crud.create_client()
        4. Gérer les erreurs (PermissionError notamment)
        5. Afficher un message de succès/échec
    """
    # TODO: Implémenter
    pass


@client.command()
def list():
    """
    Lister les clients.
    
    Flow:
        1. Vérifier connexion
        2. Appeler crud.list_clients()
        3. Afficher les résultats de manière formatée
        
    Bonus UX:
        - Si aucun client, afficher "Aucun client à afficher"
        - Afficher le nombre total de clients
        - Formater joliment (ID, nom, entreprise, contact)
    """
    # TODO: Implémenter
    pass


@client.command()
@click.argument('client_id', type=int)
def update(client_id):
    """
    Mettre à jour un client.
    
    Flow:
        1. Vérifier connexion
        2. Demander les champs à modifier (optionnels)
        3. Appeler crud.update_client() avec les kwargs
        4. Gérer PermissionError et ValueError
        
    Astuce:
        - Utiliser click.prompt() avec default='' et show_default=False
        - Ne mettre dans kwargs que les champs non vides
    """
    # TODO: Implémenter
    pass
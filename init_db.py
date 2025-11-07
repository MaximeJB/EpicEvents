"""Script d'initialisation de la base de données Epic Events.

Ce script crée toutes les tables nécessaires et insère les rôles par défaut
(sales, support, gestion) dans la base de données.

Usage:
    python init_db.py
"""

from app.db import SessionLocal, engine
from app.models import Base, Role


def init_database():
    """Crée toutes les tables et insère les rôles par défaut.

    Cette fonction :
    - Crée toutes les tables définies dans les modèles SQLAlchemy
    - Insère les trois rôles par défaut (sales, support, gestion)
    - Affiche des messages de confirmation

    Raises:
        Exception: Si la connexion à la base de données échoue
    """
    print(">> Initialisation de la base de donnees Epic Events...")
    print()

    
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables creees avec succes")
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la creation des tables : {e}")
        return

    
    db = SessionLocal()
    try:
        roles = ["sales", "support", "gestion"]
        roles_created = 0

        for role_name in roles:
            existing = db.query(Role).filter(Role.name == role_name).first()
            if not existing:
                role = Role(name=role_name)
                db.add(role)
                roles_created += 1

        db.commit()

        if roles_created > 0:
            print(f"[OK] {roles_created} role(s) cree(s) : sales, support, gestion")
        else:
            print("[INFO] Les roles existent deja dans la base de donnees")

        print()
        print("[SUCCESS] Initialisation terminee avec succes !")
        print()
        

    except Exception as e:
        db.rollback()
        print(f"[ERREUR] Erreur lors de la creation des roles : {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()

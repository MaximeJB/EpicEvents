# Epic Events CRM

Application de gestion de relation client (CRM) pour Epic Events, une entreprise d'organisation d'événements.

## 📋 Description

Epic Events CRM est une application en ligne de commande qui permet de gérer :
- Les **clients** et leurs informations de contact
- Les **contrats** associés aux clients
- Les **événements** organisés pour les clients
- Les **collaborateurs** et leurs permissions par département

L'application implémente un système de permissions basé sur les rôles (RBAC) avec trois départements :
- **Sales** (Commercial) : Gestion des clients et création d'événements
- **Support** : Gestion des événements assignés
- **Gestion** : Administration complète du système

## ✨ Fonctionnalités principales

### Menu Principal Interactif
- Interface utilisateur riche avec Rich (tableaux, panels, ASCII art)
- Navigation intuitive par menus
- Design avec bordures personnalisées et couleurs

### Gestion des Clients
- Créer un client (Sales/Gestion)
- Lister les clients (filtré selon le rôle)
- Modifier les informations client
- Recherche et affichage détaillé

### Gestion des Contrats
- Créer des contrats (Gestion uniquement)
- Lister et filtrer les contrats (signés/non signés, payés/non payés)
- Modifier les contrats (Sales pour leurs clients, Gestion pour tous)
- Signature de contrats avec notification Sentry

### Gestion des Événements
- Créer des événements pour contrats signés (Sales)
- Assigner un support à un événement (Gestion)
- Modifier les événements (Support pour les leurs, Gestion pour tous)
- Filtrer les événements sans support assigné

### Gestion des Collaborateurs
- Créer des utilisateurs (Gestion uniquement)
- Modifier les rôles et départements
- Supprimer des collaborateurs
- Système de superuser pour droits étendus

### Sécurité
- Authentification JWT avec tokens persistants
- Mots de passe hachés avec Argon2
- Principe du moindre privilège
- Protection contre injections SQL (ORM)
- Journalisation avec Sentry

## 🔧 Prérequis

- **Python** 3.9 ou supérieur
- **PostgreSQL** (ou autre base de données compatible SQLAlchemy)
- **Compte Sentry** (optionnel pour la journalisation)

## 📦 Installation

### 1. Cloner le repository

```bash
git clone https://github.com/votre-username/EpicEvents.git
cd EpicEvents
```

### 2. Créer un environnement virtuel

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/epicevents
SECRET_KEY=votre-cle-secrete-jwt-ici
ACCES_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256
SENTRY_DSN=https://votre-dsn-sentry@sentry.io/...
```

**Important** : Remplacez les valeurs par vos propres informations.

### 5. Créer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données
CREATE DATABASE epicevents;

# Créer un utilisateur (optionnel)
CREATE USER epicevents_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE epicevents TO epicevents_user;

# Quitter psql
\q
```

### 6. Initialiser la base de données

```bash
python init_db.py
```

Cette commande :
- Crée toutes les tables nécessaires
- Insère les 3 rôles par défaut (sales, support, gestion)

### 7. Créer un premier utilisateur (administrateur)

Vous devrez créer manuellement le premier utilisateur gestion directement dans la base de données ou via un script Python.

**Option 1 : Via SQL**
```sql
INSERT INTO roles (name) VALUES ('gestion') RETURNING id;
-- Notez l'ID retourné (ex: 1)

INSERT INTO users (email, password_hash, name, department, role_id, is_superuser)
VALUES (
    'admin@epicevents.com',
    '$argon2id$v=19$m=65536,t=3,p=4$...',  -- Générer avec argon2
    'Administrateur',
    'gestion',
    1,  -- ID du rôle gestion
    true
);
```

**Option 2 : Via script Python** (recommandé)

Créez un fichier `create_admin.py` :

```python
from app.db import SessionLocal
from app.models import User, Role
from app.auth import hash_password

db = SessionLocal()

role_gestion = db.query(Role).filter(Role.name == "gestion").first()
password_hash = hash_password("votre_mot_de_passe_admin")

admin = User(
    email="admin@epicevents.com",
    password_hash=password_hash,
    name="Administrateur",
    department="gestion",
    role_id=role_gestion.id,
    is_superuser=True
)

db.add(admin)
db.commit()
print(f"✓ Administrateur créé : {admin.email}")
db.close()
```

Exécutez : `python create_admin.py`

## 🚀 Utilisation

### Lancement de l'application

**Menu principal interactif** (recommandé) :
```bash
python main.py menu_principal
```

**Interface Click CLI classique** :
```bash
python main.py --help
```

### Authentification

**Se connecter** :
```bash
python main.py auth login
# Entrez votre email et mot de passe
```

**Vérifier l'utilisateur connecté** :
```bash
python main.py auth whoami
```

**Se déconnecter** :
```bash
python main.py auth logout
```

### Exemples de commandes

#### Gestion des Clients

```bash
# Créer un client (Sales/Gestion)
python main.py client create

# Lister les clients
python main.py client list

# Modifier un client
python main.py client update
```

#### Gestion des Contrats

```bash
# Créer un contrat (Gestion uniquement)
python main.py contract create

# Lister tous les contrats
python main.py contract list

# Modifier un contrat
python main.py contract update
```

#### Gestion des Événements

```bash
# Créer un événement (Sales)
python main.py event create

# Lister les événements
python main.py event list

# Modifier un événement (Support/Gestion)
python main.py event update

# Assigner un support (Gestion)
python main.py event assign-support
```

#### Gestion des Collaborateurs

```bash
# Créer un collaborateur (Gestion uniquement)
python main.py collab create

# Lister tous les collaborateurs
python main.py collab list

# Modifier un collaborateur
python main.py collab update

# Supprimer un collaborateur
python main.py collab delete
```

## 📁 Architecture du Projet

```
EpicEvents/
│
├── app/
│   ├── __init__.py
│   ├── models.py              # Modèles SQLAlchemy (User, Client, Contract, Event)
│   ├── auth.py                # Authentification JWT + Argon2
│   ├── db.py                  # Configuration base de données
│   │
│   ├── crud/                  # Opérations CRUD
│   │   ├── crud_user.py
│   │   ├── crud_client.py
│   │   ├── crud_contract.py
│   │   └── crud_event.py
│   │
│   └── views/                 # Interface CLI
│       ├── auth_cli.py        # Commandes login/logout/whoami
│       ├── client_cli.py      # Commandes client
│       ├── contract_cli.py    # Commandes contrat
│       ├── event_cli.py       # Commandes événement
│       ├── user_cli.py        # Commandes collaborateur
│       └── main_menu.py       # Menu principal interactif
│
├── tests/                     # Tests unitaires et d'intégration
│   ├── conftest.py            # Fixtures pytest
│   ├── test_auth.py
│   ├── test_models.py
│   ├── test_crud_user.py
│   ├── test_crud_client.py
│   ├── test_crud_contract.py
│   └── test_crud_event.py
│
├── main.py                    # Point d'entrée principal
├── init_db.py                 # Script d'initialisation DB
├── requirements.txt           # Dépendances Python
├── .env                       # Variables d'environnement (non versionné)
├── .gitignore
└── README.md
```

## 🧪 Tests

### Lancer tous les tests

```bash
# Activer l'environnement virtuel
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Lancer pytest
pytest -v
```

### Lancer les tests avec couverture

```bash
pytest --cov=app tests/
```

### Tests par module

```bash
# Tester l'authentification
pytest tests/test_auth.py -v

# Tester les modèles
pytest tests/test_models.py -v

# Tester les CRUD
pytest tests/test_crud_user.py -v
pytest tests/test_crud_contract.py -v
```

## 🔐 Permissions par Rôle

| Fonctionnalité | Sales (Commercial) | Support | Gestion |
|----------------|-------------------|---------|---------|
| **Clients** |
| Créer un client | ✅ (assigné auto) | ❌ | ✅ |
| Lister les clients | ✅ (ses clients) | ✅ (tous) | ✅ (tous) |
| Modifier un client | ✅ (ses clients) | ❌ | ✅ (tous) |
| **Contrats** |
| Créer un contrat | ❌ | ❌ | ✅ |
| Lister les contrats | ✅ (ses clients) | ✅ (tous) | ✅ (tous) |
| Modifier un contrat | ✅ (ses clients) | ❌ | ✅ (tous) |
| Signer un contrat | ✅ (ses clients) | ❌ | ✅ (tous) |
| **Événements** |
| Créer un événement | ✅ (ses clients) | ❌ | ❌ |
| Lister les événements | ✅ (ses clients) | ✅ (ses events) | ✅ (tous) |
| Modifier un événement | ❌ | ✅ (ses events) | ✅ (tous) |
| Assigner un support | ❌ | ❌ | ✅ |
| **Collaborateurs** |
| Créer un utilisateur | ❌ | ❌ | ✅ |
| Lister les utilisateurs | ❌ | ❌ | ✅ |
| Modifier un utilisateur | ❌ | ❌ | ✅ |
| Supprimer un utilisateur | ❌ | ❌ | ✅ |

## 🛡️ Sécurité

### Mesures de sécurité implémentées

1. **Hachage des mots de passe** : Argon2 (algorithme moderne résistant aux GPU)
2. **Authentification JWT** : Tokens avec expiration (24h par défaut)
3. **Principe du moindre privilège** : Permissions strictes par rôle
4. **Protection injection SQL** : Utilisation exclusive de l'ORM SQLAlchemy
5. **Variables d'environnement** : Données sensibles dans `.env` (non versionné)
6. **Journalisation Sentry** : Tracking des événements métier et erreurs

### Événements journalisés dans Sentry

- ✅ Toutes les exceptions inattendues (automatique)
- ✅ Création d'un collaborateur
- ✅ Modification d'un collaborateur
- ✅ Signature d'un contrat

### Bonnes pratiques

- Ne **JAMAIS** committer le fichier `.env`
- Changer le `SECRET_KEY` en production
- Utiliser un mot de passe fort pour l'administrateur
- Limiter les accès à la base de données
- Vérifier régulièrement les logs Sentry

## 📊 Modèles de Données

### User (Utilisateur)
- `id` : Identifiant unique
- `email` : Email unique
- `password_hash` : Hash Argon2
- `name` : Nom complet
- `department` : Département
- `role_id` : Clé étrangère vers Role
- `is_superuser` : Booléen (droits étendus)

### Client
- `id` : Identifiant unique
- `name` : Nom complet
- `email` : Email unique
- `phone_number` : Téléphone unique
- `company_name` : Nom de l'entreprise
- `created_at` : Date de création
- `last_update` : Dernière mise à jour
- `sales_contact_id` : Commercial assigné

### Contract (Contrat)
- `id` : Identifiant unique
- `total_amount` : Montant total (Decimal)
- `remaining_amount` : Montant restant (Decimal)
- `created_at` : Date de création
- `status` : Statut (pending/signed)
- `client_id` : Clé étrangère vers Client

### Event (Événement)
- `id` : Identifiant unique
- `start_date` : Date de début
- `end_date` : Date de fin
- `location` : Lieu
- `attendees` : Nombre de participants
- `notes` : Notes additionnelles
- `contract_id` : Clé étrangère vers Contract
- `support_contact_id` : Support assigné (nullable)

## 🐛 Dépannage

### Erreur : "No such command 'menu_principal'"

Vérifiez que vous utilisez bien :
```bash
python main.py menu_principal
```
(avec underscore, pas de tiret)

### Erreur : "Pas d'utilisateur connecté"

Connectez-vous d'abord :
```bash
python main.py auth login
```

### Erreur de connexion à la base de données

Vérifiez :
1. PostgreSQL est bien démarré
2. Le `DATABASE_URL` dans `.env` est correct
3. La base de données existe (`CREATE DATABASE epicevents;`)
4. L'utilisateur a les permissions nécessaires

### Token JWT expiré

Le token expire après 24h. Reconnectez-vous :
```bash
python main.py auth logout
python main.py auth login
```

## 📝 Développement

### Ajouter une nouvelle fonctionnalité

1. **Modèle** : Modifier `app/models.py` si nécessaire
2. **CRUD** : Ajouter les fonctions dans `app/crud/`
3. **CLI** : Ajouter les commandes dans `app/views/`
4. **Tests** : Ajouter les tests dans `tests/`

### Formater le code

```bash
# Installer black et flake8
pip install black flake8

# Formater
black app/ tests/ main.py

# Vérifier PEP8
flake8 app/ tests/ main.py --max-line-length=120
```

## 📜 Licence

Ce projet est développé dans le cadre d'un exercice de formation OpenClassrooms.

## 👤 Auteur

Maxime - Développeur Python en formation

## 🙏 Remerciements

- **SQLAlchemy** : ORM puissant pour Python
- **Click** : Framework CLI intuitif
- **Rich** : Interface CLI magnifique
- **Argon2** : Hachage sécurisé
- **Sentry** : Journalisation et monitoring
- **OpenClassrooms** : Formation et cahier des charges

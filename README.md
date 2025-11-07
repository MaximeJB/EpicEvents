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
- Lister et filtrer les contrats :
  - `--unsigned` : contrats non signés
  - `--unpaid` : contrats non entièrement payés
- Modifier les contrats (Sales pour leurs clients, Gestion pour tous)
- Signature de contrats avec notification Sentry

### Gestion des Événements
- Créer des événements pour contrats signés (Sales)
- Assigner un support à un événement (Gestion)
- Modifier les événements (Support pour les leurs, Gestion pour tous)
- Filtrer les événements :
  - `--no-support` : événements sans support assigné (Gestion)
  - `--mine` : événements qui me sont assignés (Support)

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
- **Compte Sentry**

## 📦 Installation

### 1. Cloner le repository

```bash
git clone https://github.com/MaximeJB/EpicEvents.git
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

**Option : Via script Python** 

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

## 📊 Qualité du Code

### Rapport de Tests (Pytest Coverage)

**Couverture de tests : 99%** ✅

```
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
app\auth.py                   62      1    98%   176
app\db.py                      9      0   100%
app\managers\__init__.py       0      0   100%
app\managers\client.py        29      0   100%
app\managers\contract.py      39      0   100%
app\managers\event.py         55      0   100%
app\managers\user.py          40      0   100%
app\models.py                 56      0   100%
--------------------------------------------------------
TOTAL                        290      1    99%

125 tests passed, 3 warnings in 13.91s
```

**Détails** :
- ✅ 125 tests unitaires et d'intégration
- ✅ 99% de couverture sur la logique métier (models, auth, managers)
- ✅ 100% de couverture sur tous les managers (user, client, contract, event)
- ✅ 100% de couverture sur les modèles de données

La seule ligne non couverte (ligne 176 de auth.py) concerne le cas du superuser, qui est une feature edge non utilisée actuellement.

### Rapport Flake8 (Qualité du Code)

**33 erreurs mineures détectées** (principalement des problèmes de style)

**Configuration** : Configuration souple avec règles PEP8 adaptées au projet

**Répartition des erreurs** :
- E111/E117 : Indentation (7 erreurs) - dans managers
- E251 : Espaces autour du `=` (9 erreurs) - dans models.py
- E231/E221/E222 : Espaces manquants (8 erreurs) - formatage mineur
- F401 : Imports inutilisés (5 erreurs) - imports de type hints
- E123/E126 : Indentation brackets (2 erreurs) - style
- E722 : Bare except (1 erreur) - dans auth.py
- E225 : Espace manquant autour opérateur (1 erreur)

**Note** : Ces erreurs sont mineures et n'impactent pas le fonctionnement de l'application. Elles concernent principalement le formatage du code et des imports de documentation.

**Commande pour reproduire** :
```bash
flake8 app/ tests/ main.py --statistics --count
```

**Configuration utilisée** : `.flake8` avec max-line-length=120 et règles souples

## 📜 Licence

Ce projet est développé dans le cadre d'un exercice de formation OpenClassrooms.

## 👤 Auteur

Maxime - Développeur Python en formation

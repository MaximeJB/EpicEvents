"""Modèles SQLAlchemy pour Epic Events CRM.

Ce module définit les modèles de données pour les rôles, utilisateurs,
clients, contrats et événements.
"""
from datetime import datetime, UTC
from decimal import Decimal

from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, func
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column

Base = declarative_base()


class Role(Base):
    """Modèle représentant un rôle utilisateur.

    Attributes:
        id: Identifiant unique du rôle
        name: Nom du rôle (sales, support, gestion)
        users: Liste des utilisateurs ayant ce rôle
    """
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class User(Base):
    """Modèle représentant un utilisateur du système.

    Attributes:
        id: Identifiant unique de l'utilisateur
        name: Nom complet de l'utilisateur
        email: Email unique de l'utilisateur
        password_hash: Hash Argon2 du mot de passe
        department: Département de l'utilisateur
        is_superuser: Indique si l'utilisateur a tous les droits
        role: Rôle de l'utilisateur
        role_id: Clé étrangère vers le rôle
        clients: Liste des clients assignés à cet utilisateur
        events: Liste des événements assignés à cet utilisateur (support)
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable =False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(50), nullable = True)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    role: Mapped["Role"] = relationship(back_populates="users")
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="sales_contact")
    events: Mapped[list["Event"]] = relationship("Event", back_populates="support_contact")


class Client(Base):
    """Modèle représentant un client.

    Attributes:
        id: Identifiant unique du client
        name: Nom complet du client
        phone_number: Numéro de téléphone unique
        email: Email unique du client
        company_name: Nom de l'entreprise du client
        created_at: Date de création du client
        last_update: Date de dernière mise à jour
        sales_contact_id: Clé étrangère vers l'utilisateur commercial
        sales_contact: Commercial assigné au client
        contracts: Liste des contrats du client
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    phone_number : Mapped[str] = mapped_column(String(20), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable =False)
    company_name : Mapped[str] = mapped_column(String(100), nullable=False)
    created_at : Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    last_update : Mapped[datetime] = mapped_column(onupdate=func.now(), default=lambda: datetime.now(UTC))

    sales_contact_id : Mapped[int] = mapped_column(ForeignKey("users.id"))
    sales_contact: Mapped["User"] = relationship(back_populates="clients")
    contracts: Mapped[list["Contract"]] = relationship("Contract", back_populates="client")


class Contract(Base):
    """Modèle représentant un contrat client.

    Attributes:
        id: Identifiant unique du contrat
        total_amount: Montant total du contrat
        remaining_amount: Montant restant à payer
        created_at: Date de création du contrat
        status: Statut du contrat (pending ou signed)
        client_id: Clé étrangère vers le client
        client: Client associé au contrat
        events: Liste des événements liés au contrat
    """
    __tablename__ = "contracts"

    id =  Column(Integer, primary_key=True)
    total_amount : Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    remaining_amount : Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    created_at : Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    status : Mapped[str] = mapped_column(default='pending')

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    client: Mapped["Client"] = relationship(back_populates="contracts")
    events: Mapped[list["Event"]] = relationship("Event", back_populates="contract")


class Event(Base):
    """Modèle représentant un événement.

    Attributes:
        id: Identifiant unique de l'événement
        start_date: Date et heure de début de l'événement
        end_date: Date et heure de fin de l'événement
        location: Lieu de l'événement
        attendees: Nombre de participants
        notes: Notes additionnelles sur l'événement
        support_contact: Utilisateur support assigné à l'événement
        support_contact_id: Clé étrangère vers l'utilisateur support
        contract_id: Clé étrangère vers le contrat
        contract: Contrat associé à l'événement
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)

    start_date : Mapped[datetime]
    end_date : Mapped[datetime]
    location : Mapped[str]
    attendees : Mapped[int]
    notes : Mapped[str]= mapped_column(nullable =True)

    support_contact: Mapped["User | None"] = relationship(back_populates="events")
    support_contact_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable = True)

    contract_id : Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    contract: Mapped["Contract"] = relationship(back_populates="events")

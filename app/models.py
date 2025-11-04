from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, func
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
from datetime import datetime, UTC
from decimal import Decimal 

Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship("User", back_populates="role")
    
class User(Base):
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
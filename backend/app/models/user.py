import enum
import uuid

from sqlalchemy import Column, String, Boolean, Enum, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    projektleiter = "projektleiter"
    planer = "planer"
    techniker = "techniker"
    betrachter = "betrachter"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=True, index=True)
    vorname = Column(String, nullable=True)
    nachname = Column(String, nullable=True)
    full_name = Column(String, nullable=False)  # bleibt für Abwärtskompatibilität bestehen
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.betrachter)
    abteilung = Column(String, nullable=True)
    firma = Column(String, nullable=True)
    telefon = Column(String, nullable=True)
    notiz = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    muss_passwort_aendern = Column(Boolean, default=False)
    ablauf_datum = Column(DateTime(timezone=True), nullable=True)
    letzter_login = Column(DateTime(timezone=True), nullable=True)
    fehlgeschlagene_logins = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

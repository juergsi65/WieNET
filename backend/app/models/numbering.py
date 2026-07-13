"""Konfigurierbares, transaktionssicheres Nummernvergabe-System.

Die eigentliche Nummer wird NIE im Frontend erzeugt, sondern ausschließlich über
`app.core.numbering.generate_nummer`, das den Zähler pro Schema+Geltungsbereich
mit einem einzigen atomaren `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`
erhöht (siehe core/numbering.py). Das ist unter PostgreSQL auch bei parallelen
Anfragen kollisionsfrei - im Gegensatz zu einem naiven `COUNT(*)`-basierten
Zähler (siehe FibreForge-Referenzprojekt: `Entry.query.filter(...).count()`),
der unter Nebenläufigkeit doppelte Nummern erzeugen kann.
"""
import uuid

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


def uuid_col():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Nummernschema(Base):
    """Konfiguration eines Nummernkreises für einen Objekttyp, z.B.:
    entity_type='gebiet', pattern='G-{sequence:03d}', scope='global'
    entity_type='cluster', pattern='{gebiet_code}-C-{sequence:03d}', scope='gebiet'
    Verfügbare Platzhalter im pattern: {sequence}, {gebiet_code}, {cluster_code},
    {projekt_code}, {jahr} - je nachdem, welche im jeweiligen Erstell-Kontext
    verfügbar sind (siehe core/numbering.py PATTERN_KEYS_BY_ENTITY)."""
    __tablename__ = "nummernschemata"
    id = uuid_col()
    entity_type = Column(String, nullable=False)  # gebiet | cluster | ... (siehe core/numbering.py ENTITY_TYPES)
    name = Column(String, nullable=False)
    pattern = Column(String, nullable=False)
    scope = Column(String, nullable=False, default="global")  # global | gebiet | cluster | projekt
    start_value = Column(Integer, nullable=False, default=1)
    aktiv = Column(Boolean, default=True, nullable=False)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())
    geaendert_am = Column(DateTime(timezone=True), onupdate=func.now())

    # Partieller Unique-Index statt UniqueConstraint: erzwingt "höchstens ein aktives
    # Schema je Objekttyp", erlaubt aber beliebig viele inaktive/historische Schemata.
    __table_args__ = (
        Index("uq_nummernschema_entity_aktiv", "entity_type", unique=True, postgresql_where=(aktiv == True)),  # noqa: E712
    )


class Nummernkreis(Base):
    """Der eigentliche, pro (Schema, Geltungsbereichs-Schlüssel) geführte atomare
    Zähler. scope_key ist z.B. die Gebiets-UUID als String oder 'global'."""
    __tablename__ = "nummernkreise"
    id = uuid_col()
    schema_id = Column(UUID(as_uuid=True), ForeignKey("nummernschemata.id"), nullable=False)
    scope_key = Column(String, nullable=False)
    next_value = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("schema_id", "scope_key", name="uq_nummernkreis_schema_scope"),)


class VergebeneNummer(Base):
    """Audit-Spur jeder tatsächlich vergebenen Nummer - bleibt auch nach Löschung
    des zugehörigen Objekts erhalten (Nummern werden nie stillschweigend
    wiederverwendet, siehe Aufgabenstellung Abschnitt 12)."""
    __tablename__ = "vergebene_nummern"
    id = uuid_col()
    schema_id = Column(UUID(as_uuid=True), ForeignKey("nummernschemata.id"), nullable=False)
    nummer = Column(String, nullable=False)
    objekt_typ = Column(String, nullable=False)
    objekt_id = Column(UUID(as_uuid=True), nullable=True)
    vergeben_am = Column(DateTime(timezone=True), server_default=func.now())

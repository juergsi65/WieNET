"""Material- und Herstellerkatalog: Hersteller, Produktkategorien, Produktfamilien,
Produkte, Farben (nach Farbstandard) sowie Rohrverband-/Kabelvorlagen, die im
Redlining zur Auswahl stehen.

Farb- und Produktstammdaten stammen entweder aus geprüften, offiziellen Quellen
(`benutzerdefiniert=False`, `quelle_url` gesetzt) oder werden von Anwendern selbst
angelegt (`benutzerdefiniert=True`). Es werden keine erfundenen Artikelnummern oder
Herstellerangaben gespeichert - fehlende Angaben bleiben NULL, statt geraten zu werden.
"""
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def uuid_col():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Hersteller(Base):
    __tablename__ = "hersteller"
    id = uuid_col()
    name = Column(String, nullable=False, unique=True)
    website = Column(String, nullable=True)
    quelle_url = Column(String, nullable=True)
    aktiv = Column(Boolean, default=True, nullable=False)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())
    geaendert_am = Column(DateTime(timezone=True), onupdate=func.now())

    produktfamilien = relationship("Produktfamilie", back_populates="hersteller")


class Produktkategorie(Base):
    __tablename__ = "produktkategorien"
    id = uuid_col()
    name = Column(String, nullable=False, unique=True)
    beschreibung = Column(Text, nullable=True)
    aktiv = Column(Boolean, default=True, nullable=False)

    produktfamilien = relationship("Produktfamilie", back_populates="kategorie")


class Produktfamilie(Base):
    __tablename__ = "produktfamilien"
    id = uuid_col()
    hersteller_id = Column(UUID(as_uuid=True), ForeignKey("hersteller.id"), nullable=False)
    kategorie_id = Column(UUID(as_uuid=True), ForeignKey("produktkategorien.id"), nullable=False)
    name = Column(String, nullable=False)
    beschreibung = Column(Text, nullable=True)
    quelle_url = Column(String, nullable=True)
    quelle_version = Column(String, nullable=True)
    quelle_abgerufen_am = Column(DateTime(timezone=True), nullable=True)
    aktiv = Column(Boolean, default=True, nullable=False)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())
    geaendert_am = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("hersteller_id", "name", name="uq_produktfamilie_hersteller_name"),)

    hersteller = relationship("Hersteller", back_populates="produktfamilien")
    kategorie = relationship("Produktkategorie", back_populates="produktfamilien")
    produkte = relationship("Produkt", back_populates="produktfamilie")


class Produkt(Base):
    __tablename__ = "produkte"
    id = uuid_col()
    produktfamilie_id = Column(UUID(as_uuid=True), ForeignKey("produktfamilien.id"), nullable=False)
    name = Column(String, nullable=False)
    hersteller_artikelnummer = Column(String, nullable=True)
    produkttyp = Column(String, nullable=False)  # rohrverband | einzelrohr | microduct | schutzrohr | kabel | schacht | muffe | verteiler | sonstiges
    beschreibung = Column(Text, nullable=True)
    technische_daten = Column(JSONB, nullable=True)
    aktiv = Column(Boolean, default=True, nullable=False)
    benutzerdefiniert = Column(Boolean, default=True, nullable=False)  # False = offizielle, geprüfte Herstellerangabe
    quelle_url = Column(String, nullable=True)
    quelle_abgerufen_am = Column(DateTime(timezone=True), nullable=True)
    erstellt_von_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())
    geaendert_am = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (UniqueConstraint("produktfamilie_id", "name", name="uq_produkt_familie_name"),)

    produktfamilie = relationship("Produktfamilie", back_populates="produkte")
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])
    rohrverband_vorlagen = relationship("Rohrverbandvorlage", back_populates="produkt")
    kabel_vorlagen = relationship("Kabelvorlage", back_populates="produkt")


class Farbe(Base):
    """Farbdefinition nach einem konkreten Farbstandard (z.B. DIN EN 60794-1-1,
    TIA-598-C oder ein herstellereigener Standard). Die fachliche Identität einer
    Farbe ist (farbstandard, name, streifenfarbe, streifenanzahl) - der Hex-Wert
    dient ausschließlich der UI-Darstellung und ist kein fachliches Kriterium."""
    __tablename__ = "farben"
    id = uuid_col()
    name = Column(String, nullable=False)
    kurzcode = Column(String, nullable=True)
    hex_wert = Column(String, nullable=True)
    farbstandard = Column(String, nullable=False)  # z.B. "DIN EN 60794-1-1", "TIA-598-C", "gabocom", "benutzerdefiniert"
    streifenfarbe_id = Column(UUID(as_uuid=True), ForeignKey("farben.id"), nullable=True)
    streifenanzahl = Column(Integer, default=0, nullable=False)
    aktiv = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("farbstandard", "name", "streifenfarbe_id", "streifenanzahl", name="uq_farbe_identitaet"),
    )

    streifenfarbe = relationship("Farbe", remote_side=[id])


class Rohrverbandvorlage(Base):
    """Vorlage für einen Rohrverband/Microduct-Bündel: enthält alle Einzelrohre
    (Rohrverbandvorlage-Positionen) mit Farbe, Streifen und Dimension, so wie sie im
    Redlining beim Anlegen einer Trasse automatisch als Rohrverband übernommen wird."""
    __tablename__ = "rohrverband_vorlagen"
    id = uuid_col()
    produkt_id = Column(UUID(as_uuid=True), ForeignKey("produkte.id"), nullable=True)
    name = Column(String, nullable=False)
    aussenmantel_farbe_id = Column(UUID(as_uuid=True), ForeignKey("farben.id"), nullable=True)
    rohranzahl = Column(Integer, nullable=False)
    layout_typ = Column(String, default="ring", nullable=False)  # ring | linear
    technische_daten = Column(JSONB, nullable=True)
    aktiv = Column(Boolean, default=True, nullable=False)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())

    produkt = relationship("Produkt", back_populates="rohrverband_vorlagen")
    aussenmantel_farbe = relationship("Farbe", foreign_keys=[aussenmantel_farbe_id])
    positionen = relationship(
        "RohrvorlagePosition", back_populates="vorlage", cascade="all, delete-orphan", order_by="RohrvorlagePosition.position"
    )


class RohrvorlagePosition(Base):
    __tablename__ = "rohrverband_vorlage_positionen"
    id = uuid_col()
    vorlage_id = Column(UUID(as_uuid=True), ForeignKey("rohrverband_vorlagen.id"), nullable=False)
    position = Column(Integer, nullable=False)
    rohrfarbe_id = Column(UUID(as_uuid=True), ForeignKey("farben.id"), nullable=False)
    streifenfarbe_id = Column(UUID(as_uuid=True), ForeignKey("farben.id"), nullable=True)
    streifenanzahl = Column(Integer, default=0, nullable=False)
    aussendurchmesser_mm = Column(Float, nullable=True)
    innendurchmesser_mm = Column(Float, nullable=True)

    __table_args__ = (UniqueConstraint("vorlage_id", "position", name="uq_vorlage_position"),)

    vorlage = relationship("Rohrverbandvorlage", back_populates="positionen")
    rohrfarbe = relationship("Farbe", foreign_keys=[rohrfarbe_id])
    streifenfarbe = relationship("Farbe", foreign_keys=[streifenfarbe_id])


class Kabelvorlage(Base):
    __tablename__ = "kabel_vorlagen"
    id = uuid_col()
    produkt_id = Column(UUID(as_uuid=True), ForeignKey("produkte.id"), nullable=True)
    name = Column(String, nullable=False)
    mantelfarbe_id = Column(UUID(as_uuid=True), ForeignKey("farben.id"), nullable=True)
    faseranzahl = Column(Integer, nullable=True)
    buendeladeranzahl = Column(Integer, nullable=True)
    kabeldurchmesser_mm = Column(Float, nullable=True)
    kabeltyp = Column(String, default="glasfaser", nullable=False)  # glasfaser | kupfer
    faserstandard = Column(String, nullable=True)  # z.B. "TIA-598-C"
    technische_daten = Column(JSONB, nullable=True)
    aktiv = Column(Boolean, default=True, nullable=False)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())

    produkt = relationship("Produkt", back_populates="kabel_vorlagen")
    mantelfarbe = relationship("Farbe", foreign_keys=[mantelfarbe_id])

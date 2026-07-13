import enum
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Enum, DateTime, ForeignKey, Text, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.core.database import Base


def uuid_col():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class ObjektStatus(str, enum.Enum):
    geplant = "geplant"
    aktiv = "aktiv"
    stillgelegt = "stillgelegt"
    gestoert = "gestoert"


class Bauabschnitt(Base):
    __tablename__ = "bauabschnitte"
    id = uuid_col()
    name = Column(String, nullable=False)
    status = Column(Enum(ObjektStatus), default=ObjektStatus.geplant)
    geplant_von = Column(DateTime(timezone=True), nullable=True)
    geplant_bis = Column(DateTime(timezone=True), nullable=True)
    notizen = Column(Text, nullable=True)

    trassen = relationship("Trasse", back_populates="bauabschnitt")


class Trasse(Base):
    __tablename__ = "trassen"
    id = uuid_col()
    name = Column(String, nullable=False)
    typ = Column(String, nullable=True)  # z.B. Haupttrasse, Zubringer, Hauszuführung
    status = Column(Enum(ObjektStatus), default=ObjektStatus.aktiv)
    verlegetiefe_cm = Column(Integer, nullable=True)
    oberflaeche = Column(String, nullable=True)  # Asphalt, Pflaster, Wiese...
    laenge_m = Column(Float, nullable=True)
    geometrie = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    bauabschnitt_id = Column(UUID(as_uuid=True), ForeignKey("bauabschnitte.id"), nullable=True)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"), nullable=True)  # Hauptcluster
    erstellt_von_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notizen = Column(Text, nullable=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())
    aktualisiert_am = Column(DateTime(timezone=True), onupdate=func.now())

    bauabschnitt = relationship("Bauabschnitt", back_populates="trassen")
    rohrverbaende = relationship("Rohrverband", back_populates="trasse", cascade="all, delete-orphan")
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])


class Rohrverband(Base):
    __tablename__ = "rohrverbaende"
    id = uuid_col()
    trasse_id = Column(UUID(as_uuid=True), ForeignKey("trassen.id"), nullable=False)
    bezeichnung = Column(String, nullable=False)
    vorlage_id = Column(UUID(as_uuid=True), ForeignKey("rohrverband_vorlagen.id"), nullable=True)

    trasse = relationship("Trasse", back_populates="rohrverbaende")
    rohre = relationship("Rohr", back_populates="rohrverband", cascade="all, delete-orphan", order_by="Rohr.nummer")


class RohrStatus(str, enum.Enum):
    frei = "frei"
    belegt = "belegt"
    reserviert = "reserviert"
    blockiert = "blockiert"
    beschaedigt = "beschaedigt"


class Rohr(Base):
    __tablename__ = "rohre"
    id = uuid_col()
    rohrverband_id = Column(UUID(as_uuid=True), ForeignKey("rohrverbaende.id"), nullable=False)
    nummer = Column(Integer, nullable=False)
    farbe = Column(String, nullable=False, default="#999999")  # Hex-Fallback, falls farbe_id nicht gesetzt (Altdaten)
    farbe_id = Column(UUID(as_uuid=True), ForeignKey("farben.id"), nullable=True)  # echte Farbstammdaten inkl. Streifen
    durchmesser_mm = Column(Float, nullable=True)
    typ = Column(String, nullable=True)  # Mikrorohr, Schutzrohr, Leerrohr
    status = Column(Enum(RohrStatus), default=RohrStatus.frei)

    rohrverband = relationship("Rohrverband", back_populates="rohre")
    belegungen = relationship("RohrKabelBelegung", back_populates="rohr", cascade="all, delete-orphan")


class KabelTyp(str, enum.Enum):
    glasfaser = "glasfaser"
    kupfer = "kupfer"


class Kabel(Base):
    __tablename__ = "kabel"
    id = uuid_col()
    bezeichnung = Column(String, nullable=False)
    typ = Column(Enum(KabelTyp), default=KabelTyp.glasfaser)
    fasernanzahl = Column(Integer, nullable=True)
    belegte_fasern = Column(Integer, default=0)
    laenge_m = Column(Float, nullable=True)
    hersteller = Column(String, nullable=True)
    status = Column(Enum(ObjektStatus), default=ObjektStatus.aktiv)
    fremdfaser = Column(Boolean, default=False)
    reservekabel = Column(Boolean, default=False)
    geometrie = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)
    kabelanfang_id = Column(UUID(as_uuid=True), ForeignKey("netzelemente.id"), nullable=True)
    kabelende_id = Column(UUID(as_uuid=True), ForeignKey("netzelemente.id"), nullable=True)
    vorlage_id = Column(UUID(as_uuid=True), ForeignKey("kabel_vorlagen.id"), nullable=True)
    erstellt_von_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    belegungen = relationship("RohrKabelBelegung", back_populates="kabel")


class RohrKabelBelegung(Base):
    """Verknüpft ein Kabel mit einem Rohr, inkl. Segment entlang der Trasse."""
    __tablename__ = "rohr_kabel_belegung"
    id = uuid_col()
    rohr_id = Column(UUID(as_uuid=True), ForeignKey("rohre.id"), nullable=False)
    kabel_id = Column(UUID(as_uuid=True), ForeignKey("kabel.id"), nullable=False)
    segment_start_m = Column(Float, default=0)
    segment_ende_m = Column(Float, nullable=True)

    rohr = relationship("Rohr", back_populates="belegungen")
    kabel = relationship("Kabel", back_populates="belegungen")


class NetzelementTyp(str, enum.Enum):
    olt = "olt"
    pon = "pon"
    splitter = "splitter"
    pop = "pop"
    fcp = "fcp"
    verteiler = "verteiler"
    muffe = "muffe"
    schacht = "schacht"
    kasten = "kasten"
    hausanschluss = "hausanschluss"
    gebaeude = "gebaeude"
    technikstandort = "technikstandort"


class Netzelement(Base):
    """Gemeinsames Modell für punktförmige Netz- und Tiefbauobjekte
    (Schacht, Muffe, Verteiler, FCP, OLT, PON, Hausanschluss, Gebäude, ...)."""
    __tablename__ = "netzelemente"
    id = uuid_col()
    name = Column(String, nullable=False)
    typ = Column(Enum(NetzelementTyp), nullable=False)
    status = Column(Enum(ObjektStatus), default=ObjektStatus.aktiv)
    geometrie = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    adresse = Column(String, nullable=True)
    gemeinde = Column(String, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("netzelemente.id"), nullable=True)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"), nullable=True)  # Hauptcluster
    erstellt_von_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ports_gesamt = Column(Integer, nullable=True)
    ports_belegt = Column(Integer, default=0)
    baujahr = Column(Integer, nullable=True)
    betreiber = Column(String, nullable=True)
    eigentuemer = Column(String, nullable=True)
    hersteller = Column(String, nullable=True)
    modell = Column(String, nullable=True)
    notizen = Column(Text, nullable=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())

    children = relationship("Netzelement", backref="parent", remote_side=[id])
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])


class Stoerung(Base):
    __tablename__ = "stoerungen"
    id = uuid_col()
    titel = Column(String, nullable=False)
    beschreibung = Column(Text, nullable=True)
    objekt_typ = Column(String, nullable=True)
    objekt_id = Column(UUID(as_uuid=True), nullable=True)
    offen = Column(Boolean, default=True)
    gemeldet_am = Column(DateTime(timezone=True), server_default=func.now())
    behoben_am = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = uuid_col()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    aktion = Column(String, nullable=False)
    objekt_typ = Column(String, nullable=False)
    objekt_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(Text, nullable=True)
    zeitpunkt = Column(DateTime(timezone=True), server_default=func.now())

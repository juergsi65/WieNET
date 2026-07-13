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


# ---------------------------------------------------------------------------
# Gebiet (Area)
# ---------------------------------------------------------------------------

class GebietStatus(str, enum.Enum):
    aktiv = "aktiv"
    inaktiv = "inaktiv"
    archiviert = "archiviert"


class Gebiet(Base):
    __tablename__ = "areas"
    id = uuid_col()
    nummer = Column(String, nullable=True)  # automatisch vergeben, sofern ein aktives Nummernschema existiert
    name = Column(String, nullable=False)
    kuerzel = Column(String, nullable=True)
    beschreibung = Column(Text, nullable=True)
    gebietstyp = Column(String, nullable=True)  # Bundesland, Bezirk, Gemeinde, Ausbaugebiet, ...
    status = Column(Enum(GebietStatus), default=GebietStatus.aktiv)
    geometrie = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True)
    flaeche_m2 = Column(Float, nullable=True)
    betreiber = Column(String, nullable=True)
    eigentuemer = Column(String, nullable=True)
    organisation = Column(String, nullable=True)
    ansprechpartner = Column(String, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("areas.id"), nullable=True)
    farbe = Column(String, default="#0ea5e9")
    notizen = Column(Text, nullable=True)
    erstellt_von_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    geaendert_von_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())
    geaendert_am = Column(DateTime(timezone=True), onupdate=func.now())

    children = relationship("Gebiet", backref="parent", remote_side=[id])
    clusters = relationship("Cluster", back_populates="gebiet")
    erstellt_von = relationship("User", foreign_keys=[erstellt_von_id])
    geaendert_von = relationship("User", foreign_keys=[geaendert_von_id])


# ---------------------------------------------------------------------------
# Projekt
# ---------------------------------------------------------------------------

class ProjektStatus(str, enum.Enum):
    entwurf = "entwurf"
    planung = "planung"
    genehmigung = "genehmigung"
    ausschreibung = "ausschreibung"
    bauvorbereitung = "bauvorbereitung"
    bau = "bau"
    dokumentation = "dokumentation"
    abnahme = "abnahme"
    betrieb = "betrieb"
    pausiert = "pausiert"
    abgeschlossen = "abgeschlossen"
    storniert = "storniert"
    archiviert = "archiviert"


class Projekt(Base):
    __tablename__ = "projects"
    id = uuid_col()
    name = Column(String, nullable=False)
    projektnummer = Column(String, nullable=True)
    projektcode = Column(String, nullable=True, index=True)
    beschreibung = Column(Text, nullable=True)
    status = Column(Enum(ProjektStatus), default=ProjektStatus.entwurf)
    projektart = Column(String, nullable=True)
    auftraggeber = Column(String, nullable=True)
    betreiber = Column(String, nullable=True)
    eigentuemer = Column(String, nullable=True)
    projektleiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    planer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    baufirma = Column(String, nullable=True)
    ansprechpartner = Column(String, nullable=True)
    start_datum = Column(DateTime(timezone=True), nullable=True)
    geplantes_ende = Column(DateTime(timezone=True), nullable=True)
    tatsaechliches_ende = Column(DateTime(timezone=True), nullable=True)
    budget = Column(Float, nullable=True)
    kostenstand = Column(Float, nullable=True)
    fortschritt_pct = Column(Integer, default=0)
    notizen = Column(Text, nullable=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())
    geaendert_am = Column(DateTime(timezone=True), onupdate=func.now())

    clusters = relationship("Cluster", back_populates="projekt")
    bauabschnitte = relationship("ProjektBauabschnitt", back_populates="projekt")


# ---------------------------------------------------------------------------
# Cluster
# ---------------------------------------------------------------------------

class ClusterStatus(str, enum.Enum):
    geplant = "geplant"
    aktiv = "aktiv"
    im_bau = "im_bau"
    abgeschlossen = "abgeschlossen"
    pausiert = "pausiert"
    archiviert = "archiviert"


class Cluster(Base):
    __tablename__ = "clusters"
    id = uuid_col()
    name = Column(String, nullable=False)
    nummer = Column(String, nullable=True)
    kuerzel = Column(String, nullable=True)
    beschreibung = Column(Text, nullable=True)
    typ = Column(String, nullable=True)  # FTTH-Ausbaucluster, PON-Cluster, Baucluster, ...
    status = Column(Enum(ClusterStatus), default=ClusterStatus.geplant)
    geometrie = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)
    flaeche_m2 = Column(Float, nullable=True)
    farbe = Column(String, default="#f59e0b")
    prioritaet = Column(Integer, default=3)  # 1=hoch, 5=niedrig
    gebiet_id = Column(UUID(as_uuid=True), ForeignKey("areas.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    projektleiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    planer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    baufirma = Column(String, nullable=True)
    start_datum = Column(DateTime(timezone=True), nullable=True)
    geplantes_ende = Column(DateTime(timezone=True), nullable=True)
    tatsaechliches_ende = Column(DateTime(timezone=True), nullable=True)
    budget = Column(Float, nullable=True)
    ausbauziel = Column(Integer, nullable=True)
    anzahl_geplante_anschluesse = Column(Integer, default=0)
    anzahl_aktive_anschluesse = Column(Integer, default=0)
    notizen = Column(Text, nullable=True)
    erstellt_von_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    geaendert_von_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())
    geaendert_am = Column(DateTime(timezone=True), onupdate=func.now())

    gebiet = relationship("Gebiet", back_populates="clusters")
    projekt = relationship("Projekt", back_populates="clusters")
    bauabschnitte = relationship("ProjektBauabschnitt", back_populates="cluster")
    ersteller = relationship("User", foreign_keys=[erstellt_von_id])
    bearbeiter = relationship("User", foreign_keys=[geaendert_von_id])


# ---------------------------------------------------------------------------
# Teilprojekt / Bauabschnitt (erweitert das bisherige Bauabschnitt-Konzept)
# ---------------------------------------------------------------------------

class BauabschnittStatus(str, enum.Enum):
    geplant = "geplant"
    aktiv = "aktiv"
    abgeschlossen = "abgeschlossen"
    pausiert = "pausiert"


class ProjektBauabschnitt(Base):
    """Teilprojekt/Bauabschnitt innerhalb eines Projekts bzw. Clusters,
    z.B. 'Bauabschnitt 1 Tiefbau', 'Bauabschnitt 2 Einblasen'."""
    __tablename__ = "construction_sections"
    id = uuid_col()
    name = Column(String, nullable=False)
    nummer = Column(Integer, nullable=True)
    beschreibung = Column(Text, nullable=True)
    status = Column(Enum(BauabschnittStatus), default=BauabschnittStatus.geplant)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"), nullable=True)
    verantwortlicher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    start_datum = Column(DateTime(timezone=True), nullable=True)
    ende_datum = Column(DateTime(timezone=True), nullable=True)
    fortschritt_pct = Column(Integer, default=0)
    notizen = Column(Text, nullable=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())

    projekt = relationship("Projekt", back_populates="bauabschnitte")
    cluster = relationship("Cluster", back_populates="bauabschnitte")


# ---------------------------------------------------------------------------
# Objektzuordnungen (Gebiet/Cluster/Projekt <-> Tiefbau-/Netzobjekte)
# Generisch über objekt_typ + objekt_id, um Duplizierung von Geodaten zu vermeiden.
# ---------------------------------------------------------------------------

class ZuordnungsRelation(str, enum.Enum):
    enthalten = "enthalten"   # Objekt liegt vollständig im Cluster/Gebiet
    schneidet = "schneidet"   # Objekt verläuft nur teilweise hindurch (z.B. lange Trasse)


class ObjektClusterZuordnung(Base):
    __tablename__ = "object_cluster_assignments"
    id = uuid_col()
    objekt_typ = Column(String, nullable=False)  # "trasse", "netzelement", "kabel", ...
    objekt_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"), nullable=False, index=True)
    relation = Column(Enum(ZuordnungsRelation), default=ZuordnungsRelation.enthalten)
    ist_hauptcluster = Column(Boolean, default=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())


class ObjektProjektZuordnung(Base):
    __tablename__ = "object_project_assignments"
    id = uuid_col()
    objekt_typ = Column(String, nullable=False)
    objekt_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    erstellt_am = Column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Granulares Berechtigungssystem
# ---------------------------------------------------------------------------

class Permission(str, enum.Enum):
    daten_anzeigen = "daten_anzeigen"
    daten_erstellen = "daten_erstellen"
    daten_bearbeiten = "daten_bearbeiten"
    daten_loeschen = "daten_loeschen"
    fotos_hochladen = "fotos_hochladen"
    dokumente_hochladen = "dokumente_hochladen"
    import_durchfuehren = "import_durchfuehren"
    export_durchfuehren = "export_durchfuehren"
    berichte_erstellen = "berichte_erstellen"
    projekte_erstellen = "projekte_erstellen"
    projekte_bearbeiten = "projekte_bearbeiten"
    cluster_erstellen = "cluster_erstellen"
    cluster_bearbeiten = "cluster_bearbeiten"
    benutzer_verwalten = "benutzer_verwalten"
    rollen_verwalten = "rollen_verwalten"
    audit_log_anzeigen = "audit_log_anzeigen"
    systemeinstellungen_aendern = "systemeinstellungen_aendern"
    backups_erstellen = "backups_erstellen"
    backups_wiederherstellen = "backups_wiederherstellen"


class UserGebietBerechtigung(Base):
    __tablename__ = "user_area_permissions"
    id = uuid_col()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id"), nullable=False, index=True)
    permission = Column(Enum(Permission), nullable=False)


class UserClusterBerechtigung(Base):
    __tablename__ = "user_cluster_permissions"
    id = uuid_col()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"), nullable=False, index=True)
    permission = Column(Enum(Permission), nullable=False)


class UserProjektBerechtigung(Base):
    __tablename__ = "user_project_permissions"
    id = uuid_col()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    permission = Column(Enum(Permission), nullable=False)


# ---------------------------------------------------------------------------
# Erweitertes Audit-Log (ergänzt das bestehende audit_log um Kontext-Felder)
# ---------------------------------------------------------------------------

class AuditErgebnis(str, enum.Enum):
    erfolg = "erfolg"
    fehler = "fehler"
    verweigert = "verweigert"


class AuditLogEintrag(Base):
    """Neue, erweiterte Audit-Log-Tabelle. Ersetzt funktional die einfache
    audit_log-Tabelle aus V1 (bleibt dort bestehen, wird aber nicht mehr befüllt)."""
    __tablename__ = "audit_logs"
    id = uuid_col()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    zeitpunkt = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    aktion = Column(String, nullable=False)  # z.B. "login", "cluster_erstellt", "export"
    objekt_typ = Column(String, nullable=True)
    objekt_id = Column(UUID(as_uuid=True), nullable=True)
    alter_wert = Column(Text, nullable=True)
    neuer_wert = Column(Text, nullable=True)
    # ON DELETE SET NULL: das Audit-Log muss die historische Aktion nachvollziehbar
    # halten, auch nachdem das referenzierte Gebiet/Cluster/Projekt gelöscht wurde -
    # sonst blockiert jeder frühere Audit-Eintrag (z.B. "cluster_erstellt") die
    # spätere Löschung des Objekts mit einem FK-Verstoß.
    area_id = Column(UUID(as_uuid=True), ForeignKey("areas.id", ondelete="SET NULL"), nullable=True)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    ip_adresse = Column(String, nullable=True)
    ergebnis = Column(Enum(AuditErgebnis), default=AuditErgebnis.erfolg)
    fehlerbeschreibung = Column(Text, nullable=True)

    user = relationship("User")

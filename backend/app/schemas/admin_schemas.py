import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


# --- Benutzer (erweitert) ---

class UserDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    username: Optional[str]
    vorname: Optional[str]
    nachname: Optional[str]
    full_name: str
    role: str
    abteilung: Optional[str]
    firma: Optional[str]
    telefon: Optional[str]
    notiz: Optional[str]
    is_active: bool
    muss_passwort_aendern: bool
    ablauf_datum: Optional[datetime]
    letzter_login: Optional[datetime]
    fehlgeschlagene_logins: int
    created_at: datetime


class UserCreateFull(BaseModel):
    email: str
    username: Optional[str] = None
    vorname: str
    nachname: str
    password: str
    role: str = "betrachter"
    abteilung: Optional[str] = None
    firma: Optional[str] = None
    telefon: Optional[str] = None
    notiz: Optional[str] = None
    ablauf_datum: Optional[datetime] = None
    muss_passwort_aendern: bool = True


class UserUpdate(BaseModel):
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    role: Optional[str] = None
    abteilung: Optional[str] = None
    firma: Optional[str] = None
    telefon: Optional[str] = None
    notiz: Optional[str] = None
    ablauf_datum: Optional[datetime] = None


class PasswordResetRequest(BaseModel):
    new_password: str
    muss_passwort_aendern: bool = True


class PermissionGrant(BaseModel):
    user_id: uuid.UUID
    scope_type: str  # "area" | "cluster" | "project"
    scope_id: uuid.UUID
    permission: str


# --- Gebiet ---

class GebietCreate(BaseModel):
    name: str
    kuerzel: Optional[str] = None
    beschreibung: Optional[str] = None
    gebietstyp: Optional[str] = None
    geometrie: Optional[dict] = None  # GeoJSON Polygon/MultiPolygon
    betreiber: Optional[str] = None
    eigentuemer: Optional[str] = None
    organisation: Optional[str] = None
    ansprechpartner: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    farbe: str = "#0ea5e9"
    notizen: Optional[str] = None
    nummer: Optional[str] = None  # nur relevant, falls kein aktives Nummernschema existiert


class GebietUpdate(BaseModel):
    name: Optional[str] = None
    kuerzel: Optional[str] = None
    nummer: Optional[str] = None
    beschreibung: Optional[str] = None
    gebietstyp: Optional[str] = None
    status: Optional[str] = None
    betreiber: Optional[str] = None
    eigentuemer: Optional[str] = None
    organisation: Optional[str] = None
    ansprechpartner: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    farbe: Optional[str] = None
    notizen: Optional[str] = None


class GebietOut(BaseModel):
    id: uuid.UUID
    nummer: Optional[str] = None
    name: str
    kuerzel: Optional[str]
    beschreibung: Optional[str]
    gebietstyp: Optional[str]
    status: str
    flaeche_m2: Optional[float]
    betreiber: Optional[str]
    eigentuemer: Optional[str]
    organisation: Optional[str]
    ansprechpartner: Optional[str]
    parent_id: Optional[uuid.UUID]
    farbe: str
    notizen: Optional[str]
    geometrie: Optional[dict] = None
    anzahl_cluster: int = 0


# --- Projekt ---

class ProjektCreate(BaseModel):
    name: str
    projektnummer: Optional[str] = None
    projektcode: Optional[str] = None
    beschreibung: Optional[str] = None
    status: str = "entwurf"
    projektart: Optional[str] = None
    auftraggeber: Optional[str] = None
    betreiber: Optional[str] = None
    eigentuemer: Optional[str] = None
    projektleiter_id: Optional[uuid.UUID] = None
    planer_id: Optional[uuid.UUID] = None
    baufirma: Optional[str] = None
    ansprechpartner: Optional[str] = None
    start_datum: Optional[datetime] = None
    geplantes_ende: Optional[datetime] = None
    budget: Optional[float] = None
    notizen: Optional[str] = None


class ProjektOut(BaseModel):
    id: uuid.UUID
    name: str
    projektnummer: Optional[str]
    projektcode: Optional[str]
    beschreibung: Optional[str]
    status: str
    projektart: Optional[str]
    auftraggeber: Optional[str]
    projektleiter_id: Optional[uuid.UUID]
    start_datum: Optional[datetime]
    geplantes_ende: Optional[datetime]
    budget: Optional[float]
    kostenstand: Optional[float]
    fortschritt_pct: int
    anzahl_cluster: int = 0


# --- Cluster ---

class ClusterCreate(BaseModel):
    name: str
    nummer: Optional[str] = None  # nur relevant, falls kein aktives Nummernschema existiert
    kuerzel: Optional[str] = None
    beschreibung: Optional[str] = None
    typ: Optional[str] = None
    status: str = "geplant"
    geometrie: dict  # GeoJSON Polygon/MultiPolygon - Pflicht
    farbe: str = "#f59e0b"
    prioritaet: int = 3
    gebiet_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    projektleiter_id: Optional[uuid.UUID] = None
    planer_id: Optional[uuid.UUID] = None
    baufirma: Optional[str] = None
    start_datum: Optional[datetime] = None
    geplantes_ende: Optional[datetime] = None
    budget: Optional[float] = None
    ausbauziel: Optional[int] = None
    notizen: Optional[str] = None


class ClusterUpdate(BaseModel):
    name: Optional[str] = None
    nummer: Optional[str] = None
    kuerzel: Optional[str] = None
    beschreibung: Optional[str] = None
    typ: Optional[str] = None
    status: Optional[str] = None
    farbe: Optional[str] = None
    prioritaet: Optional[int] = None
    gebiet_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    projektleiter_id: Optional[uuid.UUID] = None
    planer_id: Optional[uuid.UUID] = None
    ausbauziel: Optional[int] = None
    notizen: Optional[str] = None


class ClusterOut(BaseModel):
    id: uuid.UUID
    name: str
    nummer: Optional[str]
    kuerzel: Optional[str] = None
    beschreibung: Optional[str]
    typ: Optional[str]
    status: str
    flaeche_m2: Optional[float]
    farbe: str
    prioritaet: int
    gebiet_id: Optional[uuid.UUID]
    project_id: Optional[uuid.UUID]
    ausbauziel: Optional[int]
    anzahl_geplante_anschluesse: int
    anzahl_aktive_anschluesse: int
    geometrie: Optional[dict] = None


class ClusterMergeIds(BaseModel):
    cluster_ids: list[uuid.UUID]


class ClusterMergeVorschau(BaseModel):
    anzahl_cluster: int
    kombinierte_flaeche_m2: float
    anzahl_trassen: int
    anzahl_netzelemente: int
    unterschiedliche_gebiete: bool
    unterschiedliche_projekte: bool
    vorschlag_name: str


class ClusterMergeCreate(BaseModel):
    cluster_ids: list[uuid.UUID]
    name: str
    kuerzel: Optional[str] = None
    gebiet_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    farbe: str = "#f59e0b"


class ClusterZuordnungsVorschau(BaseModel):
    objekt_typ: str
    anzahl: int
    davon_enthalten: int
    davon_schneidend: int
    davon_bereits_anders_zugeordnet: int
    beispiel_ids: list[uuid.UUID]


class ClusterZuordnungBestaetigen(BaseModel):
    objekt_typen: list[str]  # welche Typen übernommen werden sollen, z.B. ["trasse", "netzelement"]


class ClusterStatsOut(BaseModel):
    flaeche_m2: Optional[float]
    trassenlaenge_m: float
    kabellaenge_m: float
    anzahl_schaechte: int
    anzahl_muffen: int
    anzahl_verteiler: int
    anzahl_fcp: int
    anzahl_hausanschluesse: int
    rohre_frei: int
    rohre_belegt: int
    rohrbelegung_pct: float
    fasern_frei: int
    fasern_belegt: int
    faserauslastung_pct: float
    anzahl_stoerungen: int
    bauabschnitte_geplant: int
    bauabschnitte_abgeschlossen: int


# --- Teilprojekt / Bauabschnitt ---

class BauabschnittCreate(BaseModel):
    name: str
    nummer: Optional[int] = None
    beschreibung: Optional[str] = None
    status: str = "geplant"
    project_id: uuid.UUID
    cluster_id: Optional[uuid.UUID] = None
    verantwortlicher_id: Optional[uuid.UUID] = None
    start_datum: Optional[datetime] = None
    ende_datum: Optional[datetime] = None
    notizen: Optional[str] = None


class BauabschnittOut(BaseModel):
    id: uuid.UUID
    name: str
    nummer: Optional[int]
    status: str
    project_id: uuid.UUID
    cluster_id: Optional[uuid.UUID]
    verantwortlicher_id: Optional[uuid.UUID]
    fortschritt_pct: int
    start_datum: Optional[datetime]
    ende_datum: Optional[datetime]


# --- Audit-Log ---

class AuditLogOut(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    benutzer_name: Optional[str] = None
    zeitpunkt: datetime
    aktion: str
    objekt_typ: Optional[str]
    objekt_id: Optional[uuid.UUID]
    area_id: Optional[uuid.UUID]
    cluster_id: Optional[uuid.UUID]
    project_id: Optional[uuid.UUID]
    ip_adresse: Optional[str]
    ergebnis: str
    fehlerbeschreibung: Optional[str]


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int

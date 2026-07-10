import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    muss_passwort_aendern: bool = False


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "betrachter"


class BauabschnittOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    status: str
    geplant_von: Optional[datetime] = None
    geplant_bis: Optional[datetime] = None


class TrasseOut(BaseModel):
    id: uuid.UUID
    name: str
    typ: Optional[str]
    status: str
    verlegetiefe_cm: Optional[int]
    oberflaeche: Optional[str]
    laenge_m: Optional[float]
    geometrie: dict  # GeoJSON
    bauabschnitt_id: Optional[uuid.UUID]
    notizen: Optional[str]


class NetzelementOut(BaseModel):
    id: uuid.UUID
    name: str
    typ: str
    status: str
    geometrie: dict  # GeoJSON
    adresse: Optional[str]
    gemeinde: Optional[str]
    parent_id: Optional[uuid.UUID]
    ports_gesamt: Optional[int]
    ports_belegt: Optional[int]
    baujahr: Optional[int]
    betreiber: Optional[str]
    eigentuemer: Optional[str]
    hersteller: Optional[str]
    modell: Optional[str]
    notizen: Optional[str]


class RohrOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nummer: int
    farbe: str
    durchmesser_mm: Optional[float]
    typ: Optional[str]
    status: str


class KabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bezeichnung: str
    typ: str
    fasernanzahl: Optional[int]
    belegte_fasern: int
    laenge_m: Optional[float]
    hersteller: Optional[str]
    status: str


class RohrBelegungDetail(BaseModel):
    rohr: RohrOut
    kabel: Optional[KabelOut] = None
    segment_start_m: Optional[float] = None
    segment_ende_m: Optional[float] = None


class RohrverbandDetail(BaseModel):
    id: uuid.UUID
    bezeichnung: str
    trasse_id: uuid.UUID
    rohre: list[RohrBelegungDetail]


class DashboardStats(BaseModel):
    trassen_laenge_m: float
    kabel_laenge_m: float
    anzahl_schaechte: int
    anzahl_muffen: int
    anzahl_hausanschluesse: int
    rohre_frei: int
    rohre_belegt: int
    fasern_frei: int
    fasern_belegt: int
    offene_stoerungen: int
    geplante_bauabschnitte: int


class SearchResult(BaseModel):
    id: uuid.UUID
    typ: str
    name: str
    geometrie: dict

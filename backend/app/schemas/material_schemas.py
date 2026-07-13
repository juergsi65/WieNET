import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


# --- Hersteller ---

class HerstellerCreate(BaseModel):
    name: str
    website: Optional[str] = None
    quelle_url: Optional[str] = None


class HerstellerUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    quelle_url: Optional[str] = None
    aktiv: Optional[bool] = None


class HerstellerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    website: Optional[str]
    quelle_url: Optional[str]
    aktiv: bool


# --- Produktkategorie ---

class ProduktkategorieCreate(BaseModel):
    name: str
    beschreibung: Optional[str] = None


class ProduktkategorieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    beschreibung: Optional[str]
    aktiv: bool


# --- Farbe ---

class FarbeCreate(BaseModel):
    name: str
    kurzcode: Optional[str] = None
    hex_wert: Optional[str] = None
    farbstandard: str
    streifenfarbe_id: Optional[uuid.UUID] = None
    streifenanzahl: int = 0


class FarbeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    kurzcode: Optional[str]
    hex_wert: Optional[str]
    farbstandard: str
    streifenfarbe_id: Optional[uuid.UUID]
    streifenanzahl: int
    aktiv: bool


# --- Produktfamilie ---

class ProduktfamilieCreate(BaseModel):
    hersteller_id: uuid.UUID
    kategorie_id: uuid.UUID
    name: str
    beschreibung: Optional[str] = None
    quelle_url: Optional[str] = None
    quelle_version: Optional[str] = None
    quelle_abgerufen_am: Optional[datetime] = None


class ProduktfamilieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    hersteller_id: uuid.UUID
    kategorie_id: uuid.UUID
    name: str
    beschreibung: Optional[str]
    quelle_url: Optional[str]
    quelle_version: Optional[str]
    quelle_abgerufen_am: Optional[datetime]
    aktiv: bool


# --- Produkt ---

class ProduktCreate(BaseModel):
    produktfamilie_id: uuid.UUID
    name: str
    hersteller_artikelnummer: Optional[str] = None
    produkttyp: str
    beschreibung: Optional[str] = None
    technische_daten: Optional[dict[str, Any]] = None
    benutzerdefiniert: bool = True
    quelle_url: Optional[str] = None
    quelle_abgerufen_am: Optional[datetime] = None


class ProduktUpdate(BaseModel):
    name: Optional[str] = None
    hersteller_artikelnummer: Optional[str] = None
    produkttyp: Optional[str] = None
    beschreibung: Optional[str] = None
    technische_daten: Optional[dict[str, Any]] = None
    aktiv: Optional[bool] = None


class ProduktOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    produktfamilie_id: uuid.UUID
    name: str
    hersteller_artikelnummer: Optional[str]
    produkttyp: str
    beschreibung: Optional[str]
    technische_daten: Optional[dict[str, Any]]
    aktiv: bool
    benutzerdefiniert: bool
    quelle_url: Optional[str]
    quelle_abgerufen_am: Optional[datetime]


# --- Rohrverbandvorlage ---

class RohrvorlagePositionCreate(BaseModel):
    position: int
    rohrfarbe_id: uuid.UUID
    streifenfarbe_id: Optional[uuid.UUID] = None
    streifenanzahl: int = 0
    aussendurchmesser_mm: Optional[float] = None
    innendurchmesser_mm: Optional[float] = None


class RohrvorlagePositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    position: int
    rohrfarbe_id: uuid.UUID
    streifenfarbe_id: Optional[uuid.UUID]
    streifenanzahl: int
    aussendurchmesser_mm: Optional[float]
    innendurchmesser_mm: Optional[float]


class RohrverbandvorlageCreate(BaseModel):
    produkt_id: Optional[uuid.UUID] = None
    name: str
    aussenmantel_farbe_id: Optional[uuid.UUID] = None
    layout_typ: str = "ring"
    technische_daten: Optional[dict[str, Any]] = None
    positionen: list[RohrvorlagePositionCreate]


class RohrverbandvorlageOut(BaseModel):
    id: uuid.UUID
    produkt_id: Optional[uuid.UUID]
    name: str
    aussenmantel_farbe_id: Optional[uuid.UUID]
    rohranzahl: int
    layout_typ: str
    technische_daten: Optional[dict[str, Any]]
    aktiv: bool
    positionen: list[RohrvorlagePositionOut]


# --- Kabelvorlage ---

class KabelvorlageCreate(BaseModel):
    produkt_id: Optional[uuid.UUID] = None
    name: str
    mantelfarbe_id: Optional[uuid.UUID] = None
    faseranzahl: Optional[int] = None
    buendeladeranzahl: Optional[int] = None
    kabeldurchmesser_mm: Optional[float] = None
    kabeltyp: str = "glasfaser"
    faserstandard: Optional[str] = None
    technische_daten: Optional[dict[str, Any]] = None


class KabelvorlageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    produkt_id: Optional[uuid.UUID]
    name: str
    mantelfarbe_id: Optional[uuid.UUID]
    faseranzahl: Optional[int]
    buendeladeranzahl: Optional[int]
    kabeldurchmesser_mm: Optional[float]
    kabeltyp: str
    faserstandard: Optional[str]
    technische_daten: Optional[dict[str, Any]]
    aktiv: bool

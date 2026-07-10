"""Redlining: Erfassung neuer Tiefbau-/Netzobjekte direkt auf der Karte.

Hält sich an die Standard-Netzinfrastruktur-Hierarchie:
Trasse -> Rohrverband -> Rohr <-> Kabel (über RohrKabelBelegung)
Netzelemente (Schacht, Kasten, Muffe, Verteiler, FCP, ...) als eigenständige Punktobjekte,
optional einem übergeordneten Element (parent_id) und/oder einem Hauptcluster zugeordnet.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

from app.core.database import get_db
from app.core.audit import log_action
from app.core.permissions import require_global_permission
from app.models.admin import Permission
from app.models.user import User
from app.models.infrastructure import (
    Trasse, Rohrverband, Rohr, RohrStatus, Kabel, KabelTyp, RohrKabelBelegung,
    Netzelement, NetzelementTyp, ObjektStatus,
)

router = APIRouter(prefix="/api/edit", tags=["redlining"])

# Standard-Farbpalette für Mikrorohre, nach DIN/branchenüblicher Rohrkennfarbe
# (angelehnt an die gängige 12er-Rohrfarbcodierung im Glasfaserausbau)
ROHR_FARBEN = [
    "#0033A0", "#F7941D", "#00A651", "#795548", "#7A7A7A", "#FFFFFF",
    "#ED1C24", "#000000", "#FFF200", "#92278F", "#EC008C", "#00AEEF",
]


# --- Trasse mit Rohrverband erfassen ---

class RohrDefinition(BaseModel):
    typ: str = "Mikrorohr"
    durchmesser_mm: float = 10


class TrasseCreateRedlining(BaseModel):
    name: str
    typ: Optional[str] = "Zubringer"
    status: str = "geplant"
    verlegetiefe_cm: Optional[int] = None
    oberflaeche: Optional[str] = None
    geometrie: dict  # GeoJSON LineString
    cluster_id: Optional[uuid.UUID] = None
    bauabschnitt_id: Optional[uuid.UUID] = None
    notizen: Optional[str] = None
    anzahl_rohre: int = 0  # 0 = kein Rohrverband anlegen
    rohr_definition: RohrDefinition = RohrDefinition()


@router.post("/trasse")
def create_trasse(
    payload: TrasseCreateRedlining, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.daten_erstellen)),
):
    geom = shape(payload.geometrie)
    if geom.geom_type != "LineString":
        raise HTTPException(status_code=400, detail="Trasse benötigt eine Liniengeometrie (LineString)")

    laenge_m = db.scalar(func.ST_Length(func.ST_Transform(from_shape(geom, srid=4326), 3857)))

    try:
        status_enum = ObjektStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültiger Status")

    trasse = Trasse(
        name=payload.name, typ=payload.typ, status=status_enum,
        verlegetiefe_cm=payload.verlegetiefe_cm, oberflaeche=payload.oberflaeche,
        laenge_m=round(laenge_m, 1) if laenge_m else None,
        geometrie=from_shape(geom, srid=4326),
        cluster_id=payload.cluster_id, bauabschnitt_id=payload.bauabschnitt_id,
        notizen=payload.notizen,
    )
    db.add(trasse)
    db.flush()

    rohrverband_id = None
    if payload.anzahl_rohre > 0:
        if payload.anzahl_rohre > len(ROHR_FARBEN):
            raise HTTPException(status_code=400, detail=f"Maximal {len(ROHR_FARBEN)} Rohre pro Rohrverband unterstützt")
        rv = Rohrverband(trasse_id=trasse.id, bezeichnung=f"RV-{trasse.name} ({payload.anzahl_rohre} {payload.rohr_definition.typ})")
        db.add(rv)
        db.flush()
        for i in range(payload.anzahl_rohre):
            db.add(Rohr(
                rohrverband_id=rv.id, nummer=i + 1, farbe=ROHR_FARBEN[i],
                durchmesser_mm=payload.rohr_definition.durchmesser_mm,
                typ=payload.rohr_definition.typ, status=RohrStatus.frei,
            ))
        rohrverband_id = rv.id

    db.commit()
    log_action(db, user, "trasse_erstellt", "trasse", trasse.id, neuer_wert=payload.name,
               cluster_id=payload.cluster_id, request=request)

    return {
        "id": str(trasse.id), "name": trasse.name, "laenge_m": trasse.laenge_m,
        "rohrverband_id": str(rohrverband_id) if rohrverband_id else None,
    }


# --- Netzelement (Schacht, Kasten, Muffe, Verteiler, FCP, ...) erfassen ---

class NetzelementCreateRedlining(BaseModel):
    name: str
    typ: str  # schacht | kasten | muffe | verteiler | fcp | technikstandort | hausanschluss | gebaeude
    status: str = "geplant"
    geometrie: dict  # GeoJSON Point
    adresse: Optional[str] = None
    gemeinde: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    cluster_id: Optional[uuid.UUID] = None
    ports_gesamt: Optional[int] = None
    betreiber: Optional[str] = None
    hersteller: Optional[str] = None
    modell: Optional[str] = None
    notizen: Optional[str] = None


@router.post("/netzelement")
def create_netzelement(
    payload: NetzelementCreateRedlining, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.daten_erstellen)),
):
    geom = shape(payload.geometrie)
    if geom.geom_type != "Point":
        raise HTTPException(status_code=400, detail="Netzelement benötigt eine Punktgeometrie")

    try:
        typ_enum = NetzelementTyp(payload.typ)
        status_enum = ObjektStatus(payload.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ungültiger Wert: {e}")

    el = Netzelement(
        name=payload.name, typ=typ_enum, status=status_enum,
        geometrie=from_shape(geom, srid=4326), adresse=payload.adresse, gemeinde=payload.gemeinde,
        parent_id=payload.parent_id, cluster_id=payload.cluster_id, ports_gesamt=payload.ports_gesamt,
        ports_belegt=0, betreiber=payload.betreiber, hersteller=payload.hersteller,
        modell=payload.modell, notizen=payload.notizen,
    )
    db.add(el)
    db.commit()
    db.refresh(el)
    log_action(db, user, "netzelement_erstellt", "netzelement", el.id, neuer_wert=f"{payload.typ}:{payload.name}",
               cluster_id=payload.cluster_id, request=request)
    return {"id": str(el.id), "name": el.name, "typ": el.typ.value}


# --- Kabel in einem Rohr verlegen ---

class KabelCreateRedlining(BaseModel):
    bezeichnung: str
    typ: str = "glasfaser"  # glasfaser | kupfer
    fasernanzahl: Optional[int] = None
    hersteller: Optional[str] = None
    rohr_id: uuid.UUID
    kabelanfang_id: Optional[uuid.UUID] = None
    kabelende_id: Optional[uuid.UUID] = None
    notizen: Optional[str] = None


@router.post("/kabel")
def create_kabel(
    payload: KabelCreateRedlining, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.daten_erstellen)),
):
    rohr = db.get(Rohr, payload.rohr_id)
    if not rohr:
        raise HTTPException(status_code=404, detail="Rohr nicht gefunden")
    if rohr.status == RohrStatus.belegt:
        raise HTTPException(status_code=400, detail="Rohr ist bereits belegt")
    if rohr.status in (RohrStatus.blockiert, RohrStatus.beschaedigt):
        raise HTTPException(status_code=400, detail=f"Rohr ist als '{rohr.status.value}' markiert und kann nicht belegt werden")

    trasse = db.query(Trasse).join(Rohrverband, Rohrverband.trasse_id == Trasse.id).filter(
        Rohrverband.id == rohr.rohrverband_id
    ).first()

    try:
        typ_enum = KabelTyp(payload.typ)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültiger Kabeltyp")

    kabel = Kabel(
        bezeichnung=payload.bezeichnung, typ=typ_enum, fasernanzahl=payload.fasernanzahl,
        belegte_fasern=0, laenge_m=trasse.laenge_m if trasse else None, hersteller=payload.hersteller,
        status=ObjektStatus.geplant, geometrie=trasse.geometrie if trasse else None,
        kabelanfang_id=payload.kabelanfang_id, kabelende_id=payload.kabelende_id,
    )
    db.add(kabel)
    db.flush()

    db.add(RohrKabelBelegung(rohr_id=rohr.id, kabel_id=kabel.id, segment_start_m=0, segment_ende_m=trasse.laenge_m if trasse else None))
    rohr.status = RohrStatus.belegt

    db.commit()
    log_action(db, user, "kabel_erstellt", "kabel", kabel.id, neuer_wert=payload.bezeichnung, request=request)
    return {"id": str(kabel.id), "bezeichnung": kabel.bezeichnung, "rohr_id": str(rohr.id)}


# --- Referenzdaten für Formulare (Farbpalette, verfügbare Typen) ---

@router.get("/referenzdaten")
def get_referenzdaten(_user: User = Depends(require_global_permission(Permission.daten_erstellen))):
    return {
        "rohr_farben": ROHR_FARBEN,
        "netzelement_typen": [t.value for t in NetzelementTyp],
        "objekt_status": [s.value for s in ObjektStatus],
        "kabel_typen": [t.value for t in KabelTyp],
    }

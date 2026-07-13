"""Materialkatalog: Hersteller, Produktkategorien, Produktfamilien, Produkte,
Farben sowie Rohrverband-/Kabelvorlagen. Lesen ist allen Rollen mit
'daten_anzeigen' erlaubt (wird im Redlining zur Materialauswahl gebraucht),
Schreiben/Löschen ist auf 'systemeinstellungen_aendern' beschränkt (=Admin,
siehe app/core/permissions.py ROLLEN_BASISRECHTE)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.audit import log_action
from app.core.permissions import require_global_permission
from app.models.admin import Permission
from app.models.user import User
from app.models.materials import (
    Hersteller, Produktkategorie, Produktfamilie, Produkt, Farbe,
    Rohrverbandvorlage, RohrvorlagePosition, Kabelvorlage,
)
from app.schemas.material_schemas import (
    HerstellerCreate, HerstellerUpdate, HerstellerOut,
    ProduktkategorieCreate, ProduktkategorieOut,
    FarbeCreate, FarbeOut,
    ProduktfamilieCreate, ProduktfamilieOut,
    ProduktCreate, ProduktUpdate, ProduktOut,
    RohrverbandvorlageCreate, RohrverbandvorlageOut,
    KabelvorlageCreate, KabelvorlageOut,
)

router = APIRouter(prefix="/api/admin/materialkatalog", tags=["admin-materialkatalog"])

READ = Depends(require_global_permission(Permission.daten_anzeigen))
WRITE = Depends(require_global_permission(Permission.systemeinstellungen_aendern))


# --- Hersteller ---

@router.get("/hersteller", response_model=list[HerstellerOut])
def list_hersteller(nur_aktive: bool = False, db: Session = Depends(get_db), _user: User = READ):
    q = db.query(Hersteller)
    if nur_aktive:
        q = q.filter(Hersteller.aktiv.is_(True))
    return q.order_by(Hersteller.name).all()


@router.post("/hersteller", response_model=HerstellerOut)
def create_hersteller(payload: HerstellerCreate, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    if db.query(Hersteller).filter_by(name=payload.name).first():
        raise HTTPException(status_code=400, detail="Hersteller mit diesem Namen existiert bereits")
    h = Hersteller(**payload.model_dump())
    db.add(h)
    db.commit()
    db.refresh(h)
    log_action(db, user, "hersteller_erstellt", "hersteller", h.id, neuer_wert=h.name, request=request)
    return h


@router.patch("/hersteller/{hersteller_id}", response_model=HerstellerOut)
def update_hersteller(
    hersteller_id: uuid.UUID, payload: HerstellerUpdate, request: Request,
    db: Session = Depends(get_db), user: User = WRITE,
):
    h = db.get(Hersteller, hersteller_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hersteller nicht gefunden")
    alt = h.name
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(h, field, value)
    db.commit()
    db.refresh(h)
    log_action(db, user, "hersteller_aktualisiert", "hersteller", h.id, alter_wert=alt, neuer_wert=h.name, request=request)
    return h


@router.delete("/hersteller/{hersteller_id}")
def delete_hersteller(hersteller_id: uuid.UUID, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    h = db.get(Hersteller, hersteller_id)
    if not h:
        raise HTTPException(status_code=404, detail="Hersteller nicht gefunden")
    anzahl = db.query(Produktfamilie).filter_by(hersteller_id=hersteller_id).count()
    if anzahl > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Hersteller kann nicht gelöscht werden: {anzahl} Produktfamilie(n) hängen noch an ihm. "
                   f"Zuerst Produktfamilien löschen oder Hersteller deaktivieren.",
        )
    db.delete(h)
    db.commit()
    log_action(db, user, "hersteller_geloescht", "hersteller", hersteller_id, alter_wert=h.name, request=request)
    return {"status": "geloescht"}


# --- Produktkategorien ---

@router.get("/kategorien", response_model=list[ProduktkategorieOut])
def list_kategorien(db: Session = Depends(get_db), _user: User = READ):
    return db.query(Produktkategorie).order_by(Produktkategorie.name).all()


@router.post("/kategorien", response_model=ProduktkategorieOut)
def create_kategorie(payload: ProduktkategorieCreate, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    if db.query(Produktkategorie).filter_by(name=payload.name).first():
        raise HTTPException(status_code=400, detail="Produktkategorie mit diesem Namen existiert bereits")
    k = Produktkategorie(**payload.model_dump())
    db.add(k)
    db.commit()
    db.refresh(k)
    log_action(db, user, "produktkategorie_erstellt", "produktkategorie", k.id, neuer_wert=k.name, request=request)
    return k


@router.delete("/kategorien/{kategorie_id}")
def delete_kategorie(kategorie_id: uuid.UUID, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    k = db.get(Produktkategorie, kategorie_id)
    if not k:
        raise HTTPException(status_code=404, detail="Produktkategorie nicht gefunden")
    anzahl = db.query(Produktfamilie).filter_by(kategorie_id=kategorie_id).count()
    if anzahl > 0:
        raise HTTPException(status_code=409, detail=f"Kategorie kann nicht gelöscht werden: {anzahl} Produktfamilie(n) verwenden sie noch.")
    db.delete(k)
    db.commit()
    log_action(db, user, "produktkategorie_geloescht", "produktkategorie", kategorie_id, alter_wert=k.name, request=request)
    return {"status": "geloescht"}


# --- Farben ---

@router.get("/farben", response_model=list[FarbeOut])
def list_farben(farbstandard: str | None = None, db: Session = Depends(get_db), _user: User = READ):
    q = db.query(Farbe)
    if farbstandard:
        q = q.filter(Farbe.farbstandard == farbstandard)
    return q.order_by(Farbe.farbstandard, Farbe.streifenanzahl, Farbe.name).all()


@router.post("/farben", response_model=FarbeOut)
def create_farbe(payload: FarbeCreate, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    existing = db.query(Farbe).filter_by(
        farbstandard=payload.farbstandard, name=payload.name,
        streifenfarbe_id=payload.streifenfarbe_id, streifenanzahl=payload.streifenanzahl,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Diese Farbe existiert in diesem Farbstandard bereits identisch")
    f = Farbe(**payload.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    log_action(db, user, "farbe_erstellt", "farbe", f.id, neuer_wert=f"{f.farbstandard}:{f.name}", request=request)
    return f


@router.delete("/farben/{farbe_id}")
def delete_farbe(farbe_id: uuid.UUID, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    f = db.get(Farbe, farbe_id)
    if not f:
        raise HTTPException(status_code=404, detail="Farbe nicht gefunden")
    abhaengige = (
        db.query(RohrvorlagePosition).filter(
            (RohrvorlagePosition.rohrfarbe_id == farbe_id) | (RohrvorlagePosition.streifenfarbe_id == farbe_id)
        ).count()
        + db.query(Rohrverbandvorlage).filter_by(aussenmantel_farbe_id=farbe_id).count()
        + db.query(Kabelvorlage).filter_by(mantelfarbe_id=farbe_id).count()
        + db.query(Farbe).filter_by(streifenfarbe_id=farbe_id).count()
    )
    if abhaengige > 0:
        raise HTTPException(status_code=409, detail=f"Farbe wird noch an {abhaengige} Stelle(n) verwendet und kann nicht gelöscht werden.")
    db.delete(f)
    db.commit()
    log_action(db, user, "farbe_geloescht", "farbe", farbe_id, alter_wert=f"{f.farbstandard}:{f.name}", request=request)
    return {"status": "geloescht"}


# --- Produktfamilien ---

@router.get("/produktfamilien", response_model=list[ProduktfamilieOut])
def list_produktfamilien(
    hersteller_id: uuid.UUID | None = None, kategorie_id: uuid.UUID | None = None,
    db: Session = Depends(get_db), _user: User = READ,
):
    q = db.query(Produktfamilie)
    if hersteller_id:
        q = q.filter(Produktfamilie.hersteller_id == hersteller_id)
    if kategorie_id:
        q = q.filter(Produktfamilie.kategorie_id == kategorie_id)
    return q.order_by(Produktfamilie.name).all()


@router.post("/produktfamilien", response_model=ProduktfamilieOut)
def create_produktfamilie(payload: ProduktfamilieCreate, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    if not db.get(Hersteller, payload.hersteller_id):
        raise HTTPException(status_code=404, detail="Hersteller nicht gefunden")
    if not db.get(Produktkategorie, payload.kategorie_id):
        raise HTTPException(status_code=404, detail="Produktkategorie nicht gefunden")
    if db.query(Produktfamilie).filter_by(hersteller_id=payload.hersteller_id, name=payload.name).first():
        raise HTTPException(status_code=400, detail="Produktfamilie mit diesem Namen existiert für diesen Hersteller bereits")
    pf = Produktfamilie(**payload.model_dump())
    db.add(pf)
    db.commit()
    db.refresh(pf)
    log_action(db, user, "produktfamilie_erstellt", "produktfamilie", pf.id, neuer_wert=pf.name, request=request)
    return pf


@router.delete("/produktfamilien/{familie_id}")
def delete_produktfamilie(familie_id: uuid.UUID, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    pf = db.get(Produktfamilie, familie_id)
    if not pf:
        raise HTTPException(status_code=404, detail="Produktfamilie nicht gefunden")
    anzahl = db.query(Produkt).filter_by(produktfamilie_id=familie_id).count()
    if anzahl > 0:
        raise HTTPException(status_code=409, detail=f"Produktfamilie kann nicht gelöscht werden: {anzahl} Produkt(e) hängen noch an ihr.")
    db.delete(pf)
    db.commit()
    log_action(db, user, "produktfamilie_geloescht", "produktfamilie", familie_id, alter_wert=pf.name, request=request)
    return {"status": "geloescht"}


# --- Produkte ---

@router.get("/produkte", response_model=list[ProduktOut])
def list_produkte(
    produktfamilie_id: uuid.UUID | None = None, produkttyp: str | None = None, nur_aktive: bool = False,
    db: Session = Depends(get_db), _user: User = READ,
):
    q = db.query(Produkt)
    if produktfamilie_id:
        q = q.filter(Produkt.produktfamilie_id == produktfamilie_id)
    if produkttyp:
        q = q.filter(Produkt.produkttyp == produkttyp)
    if nur_aktive:
        q = q.filter(Produkt.aktiv.is_(True))
    return q.order_by(Produkt.name).all()


@router.post("/produkte", response_model=ProduktOut)
def create_produkt(payload: ProduktCreate, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    if not db.get(Produktfamilie, payload.produktfamilie_id):
        raise HTTPException(status_code=404, detail="Produktfamilie nicht gefunden")
    if db.query(Produkt).filter_by(produktfamilie_id=payload.produktfamilie_id, name=payload.name).first():
        raise HTTPException(status_code=400, detail="Produkt mit diesem Namen existiert in dieser Produktfamilie bereits")
    p = Produkt(**payload.model_dump(), erstellt_von_id=user.id)
    db.add(p)
    db.commit()
    db.refresh(p)
    log_action(db, user, "produkt_erstellt", "produkt", p.id, neuer_wert=p.name, request=request)
    return p


@router.patch("/produkte/{produkt_id}", response_model=ProduktOut)
def update_produkt(produkt_id: uuid.UUID, payload: ProduktUpdate, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    p = db.get(Produkt, produkt_id)
    if not p:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    alt = p.name
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    log_action(db, user, "produkt_aktualisiert", "produkt", p.id, alter_wert=alt, neuer_wert=p.name, request=request)
    return p


@router.delete("/produkte/{produkt_id}")
def delete_produkt(produkt_id: uuid.UUID, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    p = db.get(Produkt, produkt_id)
    if not p:
        raise HTTPException(status_code=404, detail="Produkt nicht gefunden")
    anzahl = (
        db.query(Rohrverbandvorlage).filter_by(produkt_id=produkt_id).count()
        + db.query(Kabelvorlage).filter_by(produkt_id=produkt_id).count()
    )
    if anzahl > 0:
        raise HTTPException(status_code=409, detail=f"Produkt kann nicht gelöscht werden: {anzahl} Vorlage(n) verwenden es noch.")
    db.delete(p)
    db.commit()
    log_action(db, user, "produkt_geloescht", "produkt", produkt_id, alter_wert=p.name, request=request)
    return {"status": "geloescht"}


# --- Rohrverbandvorlagen ---

def _rohrverbandvorlage_to_out(v: Rohrverbandvorlage) -> RohrverbandvorlageOut:
    return RohrverbandvorlageOut(
        id=v.id, produkt_id=v.produkt_id, name=v.name, aussenmantel_farbe_id=v.aussenmantel_farbe_id,
        rohranzahl=v.rohranzahl, layout_typ=v.layout_typ, technische_daten=v.technische_daten, aktiv=v.aktiv,
        positionen=[
            {
                "id": p.id, "position": p.position, "rohrfarbe_id": p.rohrfarbe_id,
                "streifenfarbe_id": p.streifenfarbe_id, "streifenanzahl": p.streifenanzahl,
                "aussendurchmesser_mm": p.aussendurchmesser_mm, "innendurchmesser_mm": p.innendurchmesser_mm,
            }
            for p in v.positionen
        ],
    )


@router.get("/rohrverband-vorlagen", response_model=list[RohrverbandvorlageOut])
def list_rohrverbandvorlagen(nur_aktive: bool = False, db: Session = Depends(get_db), _user: User = READ):
    q = db.query(Rohrverbandvorlage).options(joinedload(Rohrverbandvorlage.positionen))
    if nur_aktive:
        q = q.filter(Rohrverbandvorlage.aktiv.is_(True))
    return [_rohrverbandvorlage_to_out(v) for v in q.order_by(Rohrverbandvorlage.name).all()]


@router.post("/rohrverband-vorlagen", response_model=RohrverbandvorlageOut)
def create_rohrverbandvorlage(payload: RohrverbandvorlageCreate, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    if not payload.positionen:
        raise HTTPException(status_code=400, detail="Rohrverbandvorlage benötigt mindestens eine Rohrposition")
    positionsnummern = [p.position for p in payload.positionen]
    if len(set(positionsnummern)) != len(positionsnummern):
        raise HTTPException(status_code=400, detail="Rohrpositionen müssen eindeutig sein")
    for farbe_id in {p.rohrfarbe_id for p in payload.positionen} | {p.streifenfarbe_id for p in payload.positionen if p.streifenfarbe_id}:
        if not db.get(Farbe, farbe_id):
            raise HTTPException(status_code=404, detail=f"Farbe {farbe_id} nicht gefunden")

    v = Rohrverbandvorlage(
        produkt_id=payload.produkt_id, name=payload.name, aussenmantel_farbe_id=payload.aussenmantel_farbe_id,
        rohranzahl=len(payload.positionen), layout_typ=payload.layout_typ, technische_daten=payload.technische_daten,
    )
    db.add(v)
    db.flush()
    for pos in payload.positionen:
        db.add(RohrvorlagePosition(vorlage_id=v.id, **pos.model_dump()))
    db.commit()
    db.refresh(v)
    log_action(db, user, "rohrverbandvorlage_erstellt", "rohrverbandvorlage", v.id, neuer_wert=v.name, request=request)
    return _rohrverbandvorlage_to_out(v)


@router.delete("/rohrverband-vorlagen/{vorlage_id}")
def delete_rohrverbandvorlage(vorlage_id: uuid.UUID, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    # Rohrverband (infrastructure.py) referenziert Vorlagen noch nicht (folgt in Phase 2 mit der
    # Redlining-Integration) - eine Abhängigkeitsprüfung gegen angelegte Rohrverbände ist dann hier zu ergänzen.
    v = db.get(Rohrverbandvorlage, vorlage_id)
    if not v:
        raise HTTPException(status_code=404, detail="Rohrverbandvorlage nicht gefunden")
    db.delete(v)  # RohrvorlagePosition hängt per cascade="all, delete-orphan" daran
    db.commit()
    log_action(db, user, "rohrverbandvorlage_geloescht", "rohrverbandvorlage", vorlage_id, alter_wert=v.name, request=request)
    return {"status": "geloescht"}


# --- Kabelvorlagen ---

@router.get("/kabel-vorlagen", response_model=list[KabelvorlageOut])
def list_kabelvorlagen(nur_aktive: bool = False, db: Session = Depends(get_db), _user: User = READ):
    q = db.query(Kabelvorlage)
    if nur_aktive:
        q = q.filter(Kabelvorlage.aktiv.is_(True))
    return q.order_by(Kabelvorlage.name).all()


@router.post("/kabel-vorlagen", response_model=KabelvorlageOut)
def create_kabelvorlage(payload: KabelvorlageCreate, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    if payload.mantelfarbe_id and not db.get(Farbe, payload.mantelfarbe_id):
        raise HTTPException(status_code=404, detail="Mantelfarbe nicht gefunden")
    kv = Kabelvorlage(**payload.model_dump())
    db.add(kv)
    db.commit()
    db.refresh(kv)
    log_action(db, user, "kabelvorlage_erstellt", "kabelvorlage", kv.id, neuer_wert=kv.name, request=request)
    return kv


@router.delete("/kabel-vorlagen/{vorlage_id}")
def delete_kabelvorlage(vorlage_id: uuid.UUID, request: Request, db: Session = Depends(get_db), user: User = WRITE):
    kv = db.get(Kabelvorlage, vorlage_id)
    if not kv:
        raise HTTPException(status_code=404, detail="Kabelvorlage nicht gefunden")
    db.delete(kv)
    db.commit()
    log_action(db, user, "kabelvorlage_geloescht", "kabelvorlage", vorlage_id, alter_wert=kv.name, request=request)
    return {"status": "geloescht"}

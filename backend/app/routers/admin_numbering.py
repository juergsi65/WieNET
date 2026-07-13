"""Konfiguration der Nummernkreise (Adminbereich) und Vorschau der nächsten Nummer.

Die tatsächliche Vergabe einer Nummer erfolgt ausschließlich serverseitig beim
Anlegen des jeweiligen Objekts (siehe admin_areas.py/admin_clusters.py) - hier
wird nur konfiguriert und eine unverbindliche Vorschau berechnet."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.permissions import require_global_permission
from app.core.numbering import preview_nummer, scope_key_und_kontext, ENTITY_SCOPE_KEYS
from app.models.admin import Permission
from app.models.numbering import Nummernschema, Nummernkreis
from app.models.user import User
from app.schemas.numbering_schemas import NummernschemaCreate, NummernschemaOut, NummernVorschau

router = APIRouter(prefix="/api/admin/nummernschemata", tags=["admin-nummernsystem"])


@router.get("", response_model=list[NummernschemaOut])
def list_schemata(
    entity_type: str | None = None, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    q = db.query(Nummernschema)
    if entity_type:
        q = q.filter(Nummernschema.entity_type == entity_type)
    return q.order_by(Nummernschema.entity_type, Nummernschema.erstellt_am.desc()).all()


@router.post("", response_model=NummernschemaOut)
def create_schema(
    payload: NummernschemaCreate, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.systemeinstellungen_aendern)),
):
    if payload.entity_type not in ENTITY_SCOPE_KEYS:
        raise HTTPException(status_code=400, detail=f"Unbekannter Objekttyp '{payload.entity_type}'")
    if payload.scope not in ENTITY_SCOPE_KEYS[payload.entity_type]:
        raise HTTPException(
            status_code=400,
            detail=f"Geltungsbereich '{payload.scope}' für '{payload.entity_type}' nicht unterstützt "
                   f"(erlaubt: {', '.join(sorted(ENTITY_SCOPE_KEYS[payload.entity_type]))})",
        )
    # Neues Schema wird zunächst inaktiv angelegt, falls bereits ein aktives für denselben
    # Objekttyp existiert - explizites Aktivieren über /aktivieren wechselt bewusst und
    # nachvollziehbar (Audit-Log), statt beim Anlegen überraschend das alte zu ersetzen.
    bereits_aktives = db.query(Nummernschema).filter_by(entity_type=payload.entity_type, aktiv=True).first()
    schema = Nummernschema(**payload.model_dump(), aktiv=(bereits_aktives is None))
    db.add(schema)
    db.commit()
    db.refresh(schema)
    log_action(db, user, "nummernschema_erstellt", "nummernschema", schema.id, neuer_wert=payload.name, request=request)
    return schema


@router.post("/{schema_id}/aktivieren", response_model=NummernschemaOut)
def activate_schema(
    schema_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.systemeinstellungen_aendern)),
):
    schema = db.get(Nummernschema, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Nummernschema nicht gefunden")
    db.query(Nummernschema).filter(
        Nummernschema.entity_type == schema.entity_type, Nummernschema.aktiv.is_(True)
    ).update({"aktiv": False})
    schema.aktiv = True
    db.commit()
    db.refresh(schema)
    log_action(db, user, "nummernschema_aktiviert", "nummernschema", schema.id, neuer_wert=schema.name, request=request)
    return schema


@router.delete("/{schema_id}")
def delete_schema(
    schema_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.systemeinstellungen_aendern)),
):
    schema = db.get(Nummernschema, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Nummernschema nicht gefunden")
    if schema.aktiv:
        raise HTTPException(status_code=400, detail="Aktives Schema kann nicht gelöscht werden - zuerst ein anderes aktivieren oder deaktivieren")
    if db.query(Nummernkreis).filter_by(schema_id=schema_id).count() > 0:
        raise HTTPException(status_code=409, detail="Schema wurde bereits zur Nummernvergabe verwendet und kann nicht gelöscht werden (Historie bleibt erhalten)")
    db.delete(schema)
    db.commit()
    log_action(db, user, "nummernschema_geloescht", "nummernschema", schema_id, alter_wert=schema.name, request=request)
    return {"status": "geloescht"}


@router.get("/vorschau/{entity_type}", response_model=NummernVorschau)
def vorschau(
    entity_type: str, gebiet_id: uuid.UUID | None = None, cluster_id: uuid.UUID | None = None,
    projekt_id: uuid.UUID | None = None, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    schema = db.query(Nummernschema).filter_by(entity_type=entity_type, aktiv=True).first()
    if not schema:
        return NummernVorschau(nummer=None, hinweis="Kein aktives Nummernschema für diesen Objekttyp - Nummer bleibt frei editierbar.")

    try:
        scope_key, kontext = scope_key_und_kontext(db, schema.scope, gebiet_id, cluster_id, projekt_id)
    except ValueError as e:
        return NummernVorschau(nummer=None, hinweis=str(e))
    try:
        return NummernVorschau(nummer=preview_nummer(db, schema, scope_key, kontext))
    except ValueError as e:
        return NummernVorschau(nummer=None, hinweis=str(e))

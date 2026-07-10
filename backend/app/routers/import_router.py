import json
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, Point

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import UserRole
from app.models.infrastructure import Netzelement, NetzelementTyp, ObjektStatus

router = APIRouter(prefix="/api/import", tags=["import"])

MAX_UPLOAD_MB = 20


@router.post("/preview")
async def preview_import(
    file: UploadFile = File(...),
    _user=Depends(require_roles(UserRole.admin, UserRole.planer)),
):
    """Schritt 2-3 des Assistenten: Datei einlesen und Vorschau + erkannte Spalten liefern."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Datei überschreitet {MAX_UPLOAD_MB} MB")

    filename = file.filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(pd.io.common.BytesIO(content))
        rows = json.loads(df.head(20).to_json(orient="records"))
        return {"typ": "tabelle", "spalten": list(df.columns), "vorschau": rows, "anzahl_zeilen": len(df)}

    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(pd.io.common.BytesIO(content))
        rows = json.loads(df.head(20).to_json(orient="records"))
        return {"typ": "tabelle", "spalten": list(df.columns), "vorschau": rows, "anzahl_zeilen": len(df)}

    if filename.endswith(".geojson") or filename.endswith(".json"):
        data = json.loads(content)
        features = data.get("features", [])
        return {
            "typ": "geojson",
            "anzahl_zeilen": len(features),
            "vorschau": features[:20],
            "erkannte_eigenschaften": list(features[0]["properties"].keys()) if features else [],
        }

    raise HTTPException(status_code=400, detail="Nicht unterstütztes Dateiformat. Erlaubt: CSV, Excel, GeoJSON.")


@router.post("/commit")
async def commit_import(
    file: UploadFile = File(...),
    objekt_typ: str = Form(...),  # z.B. "schacht", "muffe", "hausanschluss"
    spalten_mapping: str = Form(...),  # JSON: {"name": "Bezeichnung", "lat": "Breite", "lon": "Laenge", ...}
    db: Session = Depends(get_db),
    _user=Depends(require_roles(UserRole.admin, UserRole.planer)),
):
    """Schritt 6-8: Validierung + tatsächlicher Import. Fehlerhafte Zeilen werden übersprungen und gemeldet."""
    content = await file.read()
    filename = file.filename.lower()
    mapping = json.loads(spalten_mapping)

    try:
        typ_enum = NetzelementTyp(objekt_typ)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unbekannter Objekttyp: {objekt_typ}")

    fehler = []
    importiert = 0

    if filename.endswith((".csv", ".xlsx", ".xls")):
        df = pd.read_csv(pd.io.common.BytesIO(content)) if filename.endswith(".csv") else pd.read_excel(pd.io.common.BytesIO(content))
        for idx, row in df.iterrows():
            try:
                name = str(row[mapping["name"]])
                lat = float(row[mapping["lat"]])
                lon = float(row[mapping["lon"]])
                if not name or name == "nan":
                    raise ValueError("Name fehlt")
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Ungültige Koordinaten")

                el = Netzelement(
                    name=name, typ=typ_enum, status=ObjektStatus.aktiv,
                    geometrie=from_shape(Point(lon, lat), srid=4326),
                    adresse=str(row.get(mapping.get("adresse", ""), "")) if mapping.get("adresse") else None,
                )
                db.add(el)
                importiert += 1
            except Exception as e:
                fehler.append({"zeile": idx + 2, "fehler": str(e)})

    elif filename.endswith((".geojson", ".json")):
        data = json.loads(content)
        for idx, feat in enumerate(data.get("features", [])):
            try:
                geom = shape(feat["geometry"])
                if geom.geom_type != "Point":
                    raise ValueError("Nur Punktgeometrien werden für diesen Objekttyp unterstützt")
                props = feat.get("properties", {})
                name = props.get(mapping.get("name", "name"), f"Objekt {idx+1}")

                el = Netzelement(
                    name=str(name), typ=typ_enum, status=ObjektStatus.aktiv,
                    geometrie=from_shape(geom, srid=4326),
                )
                db.add(el)
                importiert += 1
            except Exception as e:
                fehler.append({"zeile": idx + 1, "fehler": str(e)})
    else:
        raise HTTPException(status_code=400, detail="Nicht unterstütztes Dateiformat")

    db.commit()
    return {"importiert": importiert, "fehler": fehler, "erfolgreich": len(fehler) == 0}

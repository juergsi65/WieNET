import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.infrastructure import Rohrverband, Trasse
from app.schemas.schemas import RohrverbandDetail, RohrBelegungDetail, RohrOut, KabelOut

router = APIRouter(prefix="/api/rohrbelegung", tags=["rohrbelegung"])


@router.get("/trasse/{trasse_id}", response_model=list[RohrverbandDetail])
def get_rohrbelegung_fuer_trasse(trasse_id: uuid.UUID, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    trasse = db.get(Trasse, trasse_id)
    if not trasse:
        raise HTTPException(status_code=404, detail="Trasse nicht gefunden")

    result = []
    for rv in trasse.rohrverbaende:
        rohre_out = []
        for rohr in rv.rohre:
            belegung = rohr.belegungen[0] if rohr.belegungen else None
            rohre_out.append(RohrBelegungDetail(
                rohr=RohrOut.model_validate(rohr),
                kabel=KabelOut.model_validate(belegung.kabel) if belegung else None,
                segment_start_m=belegung.segment_start_m if belegung else None,
                segment_ende_m=belegung.segment_ende_m if belegung else None,
            ))
        result.append(RohrverbandDetail(
            id=rv.id, bezeichnung=rv.bezeichnung, trasse_id=rv.trasse_id, rohre=rohre_out,
        ))
    return result


@router.get("/rohrverband/{rohrverband_id}", response_model=RohrverbandDetail)
def get_rohrverband_detail(rohrverband_id: uuid.UUID, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    rv = db.get(Rohrverband, rohrverband_id)
    if not rv:
        raise HTTPException(status_code=404, detail="Rohrverband nicht gefunden")

    rohre_out = []
    for rohr in rv.rohre:
        belegung = rohr.belegungen[0] if rohr.belegungen else None
        rohre_out.append(RohrBelegungDetail(
            rohr=RohrOut.model_validate(rohr),
            kabel=KabelOut.model_validate(belegung.kabel) if belegung else None,
            segment_start_m=belegung.segment_start_m if belegung else None,
            segment_ende_m=belegung.segment_ende_m if belegung else None,
        ))
    return RohrverbandDetail(id=rv.id, bezeichnung=rv.bezeichnung, trasse_id=rv.trasse_id, rohre=rohre_out)

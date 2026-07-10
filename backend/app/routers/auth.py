from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.core.audit import log_action
from app.models.user import User
from app.models.admin import AuditErgebnis
from app.schemas.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

MAX_FEHLGESCHLAGENE_LOGINS = 5


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        if user:
            user.fehlgeschlagene_logins = (user.fehlgeschlagene_logins or 0) + 1
            db.commit()
        log_action(db, user, "login_fehlgeschlagen", request=request, ergebnis=AuditErgebnis.fehler)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-Mail oder Passwort falsch")

    if not user.is_active:
        log_action(db, user, "login_verweigert_deaktiviert", request=request, ergebnis=AuditErgebnis.verweigert)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Benutzer ist deaktiviert")

    if (user.fehlgeschlagene_logins or 0) >= MAX_FEHLGESCHLAGENE_LOGINS:
        log_action(db, user, "login_verweigert_gesperrt", request=request, ergebnis=AuditErgebnis.verweigert)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Konto wegen zu vieler fehlgeschlagener Anmeldeversuche gesperrt. Bitte Administrator kontaktieren.",
        )

    if user.ablauf_datum and user.ablauf_datum < datetime.now(timezone.utc):
        log_action(db, user, "login_verweigert_abgelaufen", request=request, ergebnis=AuditErgebnis.verweigert)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Zugang ist abgelaufen.")

    user.fehlgeschlagene_logins = 0
    user.letzter_login = datetime.now(timezone.utc)
    db.commit()

    log_action(db, user, "login", request=request)

    token = create_access_token(subject=user.email)
    return TokenResponse(
        access_token=token, role=user.role.value, full_name=user.full_name,
        muss_passwort_aendern=user.muss_passwort_aendern,
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user

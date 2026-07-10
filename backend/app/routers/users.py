from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles, hash_password
from app.models.user import User, UserRole
from app.schemas.schemas import UserOut, UserCreate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _admin=Depends(require_roles(UserRole.admin))):
    return db.query(User).all()


@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _admin=Depends(require_roles(UserRole.admin))):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="E-Mail bereits vergeben")
    try:
        role = UserRole(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültige Rolle")

    user = User(
        email=payload.email, full_name=payload.full_name,
        hashed_password=hash_password(payload.password), role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def deactivate_user(user_id: str, db: Session = Depends(get_db), _admin=Depends(require_roles(UserRole.admin))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    user.is_active = False
    db.commit()
    return {"status": "deaktiviert"}

"""Richtet beim allerersten Start des Systems den initialen Administrator-Zugang ein.

Dies ist KEIN Demodaten-Generator. Es werden keine Beispiel-Trassen, -Cluster,
-Projekte oder Zusatzbenutzer angelegt - das System startet mit einer leeren
Datenbank, bereit für echte Infrastrukturdaten (Import oder manuelle Erfassung).

Idempotent: läuft bei jedem Containerstart, legt den Administrator aber nur an,
falls noch kein Benutzer mit der konfigurierten ADMIN_EMAIL existiert.
"""
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


def run():
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if existing_admin:
            print(f"[bootstrap] Administrator-Konto existiert bereits: {settings.ADMIN_EMAIL}")
            return

        db.add(User(
            email=settings.ADMIN_EMAIL,
            vorname="Administrator",
            nachname="",
            full_name="Administrator",
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            role=UserRole.admin,
            muss_passwort_aendern=True,
        ))
        db.commit()
        print(f"[bootstrap] Administrator-Konto angelegt: {settings.ADMIN_EMAIL}")
        print("[bootstrap] Passwortänderung beim ersten Login ist erzwungen.")
    finally:
        db.close()


if __name__ == "__main__":
    run()

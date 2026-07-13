"""Transaktionssichere Nummernvergabe.

generate_nummer() erhöht den Zähler für ein Schema+Geltungsbereich mit EINEM
atomaren SQL-Statement (INSERT ... ON CONFLICT DO UPDATE ... RETURNING). Das ist
unter PostgreSQL kollisionsfrei, auch wenn mehrere Anfragen exakt gleichzeitig
dieselbe Nummer anfordern - PostgreSQL serialisiert konkurrierende UPDATEs auf
dieselbe Zeile automatisch über Zeilensperren, es ist also KEIN zusätzliches
SELECT ... FOR UPDATE oder Application-Level-Locking nötig.

Bewusst NICHT verwendet: `db.query(Modell).filter(...).count()` gefolgt von
`count + 1` - das ist die im FibreForge-Referenzprojekt (app.py, save_point())
verwendete Methode und race-conditioned unter Nebenläufigkeit: zwei parallele
Anfragen können denselben COUNT lesen, bevor eine von beiden committet, und
damit dieselbe Nummer erzeugen.
"""
import datetime
import re
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.numbering import Nummernschema

# Für jeden Objekttyp die im pattern erlaubten Platzhalter außer {sequence}
# (immer verfügbar) - verhindert, dass ein Schema einen im jeweiligen
# Erstell-Kontext gar nicht befüllbaren Platzhalter referenziert.
ENTITY_SCOPE_KEYS = {
    "gebiet": {"global"},
    "cluster": {"global", "gebiet", "projekt"},
    "projekt": {"global"},
    "bauabschnitt": {"global", "projekt", "cluster"},
    "trasse": {"global", "cluster", "gebiet"},
}

_PLACEHOLDER_RE = re.compile(r"\{(\w+)(?::[^}]*)?\}")


def validate_pattern(entity_type: str, pattern: str) -> None:
    if "__" in pattern:
        raise ValueError("Ungültiges Muster: '__' ist aus Sicherheitsgründen nicht erlaubt")
    if not pattern.strip():
        raise ValueError("Muster darf nicht leer sein")
    if "{sequence" not in pattern:
        raise ValueError("Muster muss den Platzhalter {sequence} enthalten (z.B. {sequence:03d})")
    erlaubt = {"sequence", "gebiet_code", "cluster_code", "projekt_code", "jahr"}
    for key in _PLACEHOLDER_RE.findall(pattern):
        if key not in erlaubt:
            raise ValueError(f"Unbekannter Platzhalter '{{{key}}}' im Muster")


def preview_nummer(db: Session, schema: Nummernschema, scope_key: str, kontext: dict) -> str:
    """Zeigt die NÄCHSTE Nummer, OHNE den Zähler zu erhöhen (für die
    Vorschau im Adminbereich vor dem tatsächlichen Anlegen)."""
    row = db.execute(
        text("SELECT next_value FROM nummernkreise WHERE schema_id = :sid AND scope_key = :sk"),
        {"sid": str(schema.id), "sk": scope_key},
    ).first()
    sequence = row[0] if row else schema.start_value
    return _format(schema.pattern, sequence, kontext)


def generate_nummer(db: Session, schema: Nummernschema, scope_key: str, kontext: dict) -> str:
    """Erhöht den Zähler atomar und gibt die neu vergebene Nummer zurück. Muss
    innerhalb derselben Transaktion wie das Anlegen des Objekts aufgerufen werden
    (kein eigenständiges commit hier) - schlägt die äußere Transaktion fehl, wird
    auch der Zählerstand zurückgerollt, es entsteht keine Lücke ohne Grund."""
    row = db.execute(
        text(
            """
            INSERT INTO nummernkreise (id, schema_id, scope_key, next_value)
            VALUES (gen_random_uuid(), :sid, :sk, :start + 1)
            ON CONFLICT (schema_id, scope_key)
            DO UPDATE SET next_value = nummernkreise.next_value + 1
            RETURNING next_value - 1
            """
        ),
        {"sid": str(schema.id), "sk": scope_key, "start": schema.start_value},
    ).first()
    sequence = row[0]
    return _format(schema.pattern, sequence, kontext)


def _format(pattern: str, sequence: int, kontext: dict) -> str:
    werte = {"sequence": sequence, **kontext}
    try:
        return pattern.format(**werte)
    except (KeyError, IndexError) as e:
        raise ValueError(f"Muster referenziert einen im Kontext nicht verfügbaren Platzhalter: {e}")


def get_active_schema(db: Session, entity_type: str) -> Nummernschema | None:
    return db.query(Nummernschema).filter_by(entity_type=entity_type, aktiv=True).first()


def scope_key_und_kontext(
    db: Session, scope: str,
    gebiet_id: uuid.UUID | None = None, cluster_id: uuid.UUID | None = None, projekt_id: uuid.UUID | None = None,
) -> tuple[str, dict]:
    """Löst aus dem konfigurierten Geltungsbereich eines Schemas den konkreten
    Zähler-Schlüssel (z.B. 'gebiet:<uuid>') sowie die im pattern verfügbaren
    Platzhalterwerte (gebiet_code/cluster_code/projekt_code/jahr) auf."""
    from app.models.admin import Gebiet, Cluster, Projekt

    kontext: dict = {"jahr": datetime.date.today().year}

    if scope == "global":
        return "global", kontext

    if scope == "gebiet":
        if not gebiet_id:
            raise ValueError("Für dieses Nummernschema wird eine Gebiets-Zuordnung benötigt")
        g = db.get(Gebiet, gebiet_id)
        if not g:
            raise ValueError("Gebiet nicht gefunden")
        kontext["gebiet_code"] = g.kuerzel or g.nummer or str(g.id)[:8]
        return f"gebiet:{gebiet_id}", kontext

    if scope == "cluster":
        if not cluster_id:
            raise ValueError("Für dieses Nummernschema wird eine Cluster-Zuordnung benötigt")
        c = db.get(Cluster, cluster_id)
        if not c:
            raise ValueError("Cluster nicht gefunden")
        kontext["cluster_code"] = c.kuerzel or c.nummer or str(c.id)[:8]
        return f"cluster:{cluster_id}", kontext

    if scope == "projekt":
        if not projekt_id:
            raise ValueError("Für dieses Nummernschema wird eine Projekt-Zuordnung benötigt")
        p = db.get(Projekt, projekt_id)
        if not p:
            raise ValueError("Projekt nicht gefunden")
        kontext["projekt_code"] = p.projektcode or p.projektnummer or str(p.id)[:8]
        return f"projekt:{projekt_id}", kontext

    raise ValueError(f"Unbekannter Geltungsbereich '{scope}'")

"""Legt die Grundausstattung des Materialkatalogs an: die zwei in der Glasfaser-/
Tiefbaubranche etablierten, öffentlich dokumentierten Farbstandards (DIN EN 60794-1-1
für Rohr-/Aderfarben, TIA-598-C für Faserfarben), ein Hersteller-Gerüst für gabocom
(gabo Systemtechnik GmbH), Hexatronic und Prysmian sowie generische, produktneutrale
Rohrverbandvorlagen für gängige Rohranzahlen.

WICHTIG: Es werden bewusst KEINE Hersteller-Artikelnummern, keine konkreten
Produktvarianten und keine exakten technischen Maße erfunden. Alle Hersteller und
Produktkategorien sind als Gerüst angelegt, damit ein Administrator sie im
Materialkatalog (Adminbereich) mit tatsächlich verifizierten Herstellerdaten
(Datenblatt, offizielle Artikelnummer) vervollständigen kann. Die generischen
Rohrverbandvorlagen sind bewusst NICHT einem Produkt zugeordnet (produkt_id=NULL) -
sie bilden nur die öffentliche DIN-Farbfolge ab, keinen Herstelleranspruch.

Idempotent: läuft bei jedem Containerstart, legt aber nichts doppelt an und
überschreibt keine bereits vorhandenen/geänderten Datensätze.
"""
from app.core.database import SessionLocal
from app.models import user, infrastructure, admin  # noqa: F401 - registriert Modelle fuer String-Relationship-Aufloesung
from app.models.materials import (
    Hersteller, Produktkategorie, Farbe, Rohrverbandvorlage, RohrvorlagePosition,
)

# DIN EN 60794-1-1 / VDE 0888 - in der deutschen Tiefbau-/Glasfaserbranche
# etablierte 12er-Kernfarbfolge für Adern, Bündeladern und Rohre.
DIN_12_FARBEN = [
    ("Rot", "RD", "#DC2626"), ("Grün", "GN", "#16A34A"), ("Blau", "BU", "#2563EB"),
    ("Gelb", "YE", "#EAB308"), ("Weiß", "WH", "#F8FAFC"), ("Grau", "GY", "#94A3B8"),
    ("Braun", "BN", "#795548"), ("Violett", "VT", "#7C3AED"), ("Türkis", "TQ", "#06B6D4"),
    ("Schwarz", "BK", "#0F172A"), ("Orange", "OG", "#EA580C"), ("Rosa", "PK", "#EC4899"),
]

# TIA-598-C - in Nordamerika/international verbreiteter 12er-Faserfarbcode.
TIA_598_C_FARBEN = [
    ("Blue", "BU", "#2563EB"), ("Orange", "OG", "#EA580C"), ("Green", "GN", "#16A34A"),
    ("Brown", "BN", "#795548"), ("Slate", "SL", "#64748B"), ("White", "WH", "#F8FAFC"),
    ("Red", "RD", "#DC2626"), ("Black", "BK", "#0F172A"), ("Yellow", "YE", "#EAB308"),
    ("Violet", "VI", "#7C3AED"), ("Rose", "RS", "#EC4899"), ("Aqua", "AQ", "#06B6D4"),
]

HERSTELLER_SEED = [
    {"name": "gabo Systemtechnik GmbH (gabocom)", "website": "https://www.gabocom.com/"},
    {"name": "Hexatronic", "website": "https://www.hexatronic.com/"},
    {"name": "Prysmian Group", "website": "https://www.prysmiangroup.com/"},
]

KATEGORIEN_SEED = [
    ("Rohrverband", "Mehrfach-Rohrverband/Bündel aus mehreren Einzelrohren (Microducts)."),
    ("Einzelrohr / Microduct", "Einzelnes Kabelschutz-/Einblasrohr."),
    ("Schutzrohr", "Stabiles Schutzrohr für Tiefbau, z.B. HDPE/PVC."),
    ("Glasfaserkabel", "Glasfaser-Außen- oder Innenkabel."),
    ("Kupferkabel", "Kupfer-Telekommunikationskabel."),
    ("Schacht", "Kabel-/Revisionsschacht."),
    ("Muffe", "Spleiß- oder Verteilmuffe."),
    ("Verteiler", "Verteilerkasten, FCP oder Abschlusspunkt."),
]

# Generische, produktneutrale Rohrverband-Layouts nach DIN-Farbfolge - keine
# Herstellerangabe, keine Artikelnummer, nur die öffentliche Farbreihenfolge.
GENERISCHE_ROHRVERBAENDE = [
    ("Generischer Rohrverband 4x10mm (DIN-Farbfolge)", 4, 10.0, 8.0),
    ("Generischer Rohrverband 7x10mm (DIN-Farbfolge)", 7, 10.0, 8.0),
    ("Generischer Rohrverband 12x10mm (DIN-Farbfolge)", 12, 10.0, 8.0),
]


def _seed_farbstandard(db, standard: str, basisfarben: list[tuple[str, str, str]]) -> list["Farbe"]:
    """Legt die 12 Basisfarben eines Standards an und erweitert sie programmatisch um
    12 Streifenkombinationen (Basisfarbe[i] mit Streifenfarbe[i+1]) - branchenübliche
    Praxis zur Kennzeichnung von Bündeln/Rohren >12, jeweils als eigene, direkt
    auswählbare Farbe. Gibt die Liste der 12 Basisfarben-Objekte zurück (Index 0-11),
    aus denen sich Rohrverband-Positionen ableiten lassen."""
    basis_objekte: list[Farbe] = []

    for name, kurzcode, hex_wert in basisfarben:
        existing = db.query(Farbe).filter_by(
            farbstandard=standard, name=name, streifenfarbe_id=None, streifenanzahl=0
        ).first()
        if not existing:
            existing = Farbe(
                name=name, kurzcode=kurzcode, hex_wert=hex_wert, farbstandard=standard,
                streifenfarbe_id=None, streifenanzahl=0,
            )
            db.add(existing)
            db.flush()
        basis_objekte.append(existing)

    for i in range(12):
        basis, streifen = basis_objekte[i], basis_objekte[(i + 1) % 12]
        existing = db.query(Farbe).filter_by(
            farbstandard=standard, name=basis.name, streifenfarbe_id=streifen.id, streifenanzahl=1
        ).first()
        if not existing:
            db.add(Farbe(
                name=basis.name, kurzcode=f"{basis.kurzcode}/{streifen.kurzcode}", hex_wert=basis.hex_wert,
                farbstandard=standard, streifenfarbe_id=streifen.id, streifenanzahl=1,
            ))

    return basis_objekte


def run():
    db = SessionLocal()
    try:
        din_basisfarben = _seed_farbstandard(db, "DIN EN 60794-1-1", DIN_12_FARBEN)
        _seed_farbstandard(db, "TIA-598-C", TIA_598_C_FARBEN)
        db.commit()
        print("[seed_materials] Farbstandards DIN EN 60794-1-1 und TIA-598-C angelegt (24 Farben je Standard).")

        for h in HERSTELLER_SEED:
            if not db.query(Hersteller).filter_by(name=h["name"]).first():
                db.add(Hersteller(name=h["name"], website=h["website"], quelle_url=h["website"]))
                print(f"[seed_materials] Hersteller angelegt: {h['name']}")
        db.commit()

        for name, beschreibung in KATEGORIEN_SEED:
            if not db.query(Produktkategorie).filter_by(name=name).first():
                db.add(Produktkategorie(name=name, beschreibung=beschreibung))
                print(f"[seed_materials] Produktkategorie angelegt: {name}")
        db.commit()

        for name, anzahl, aussen_d, innen_d in GENERISCHE_ROHRVERBAENDE:
            existing = db.query(Rohrverbandvorlage).filter_by(name=name).first()
            if existing:
                continue
            if anzahl > 12:
                raise ValueError("Generische Vorlagen >12 Rohre benötigen die Streifenkombinationen (nicht implementiert)")
            vorlage = Rohrverbandvorlage(
                produkt_id=None, name=name, aussenmantel_farbe_id=None,
                rohranzahl=anzahl, layout_typ="ring", technische_daten=None,
            )
            db.add(vorlage)
            db.flush()
            for pos in range(1, anzahl + 1):
                farbe = din_basisfarben[pos - 1]
                db.add(RohrvorlagePosition(
                    vorlage_id=vorlage.id, position=pos,
                    rohrfarbe_id=farbe.id, streifenfarbe_id=None, streifenanzahl=0,
                    aussendurchmesser_mm=aussen_d, innendurchmesser_mm=innen_d,
                ))
            print(f"[seed_materials] Rohrverbandvorlage angelegt: {name}")
        db.commit()
        print("[seed_materials] Fertig. Hersteller/Produktfamilien/Produkte mit verifizierten "
              "Herstellerangaben bitte über den Materialkatalog im Adminbereich ergänzen.")
    finally:
        db.close()


if __name__ == "__main__":
    run()

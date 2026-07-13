"""Material- und Herstellerkatalog

Neue, rein additive Tabellen für Hersteller, Produktkategorien, Produktfamilien,
Produkte, Farben (nach Farbstandard) sowie Rohrverband-/Kabelvorlagen. Keine
bestehende Tabelle wird verändert oder gelöscht - die Verknüpfung von Rohren/Kabeln
mit konkreten Produkten/Farben folgt in einer späteren Migration, sobald das
Redlining sie tatsächlich verwendet.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hersteller",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("quelle_url", sa.String(), nullable=True),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("geaendert_am", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_hersteller_name"),
    )

    op.create_table(
        "produktkategorien",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("beschreibung", sa.Text(), nullable=True),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("name", name="uq_produktkategorie_name"),
    )

    op.create_table(
        "farben",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kurzcode", sa.String(), nullable=True),
        sa.Column("hex_wert", sa.String(), nullable=True),
        sa.Column("farbstandard", sa.String(), nullable=False),
        sa.Column("streifenfarbe_id", UUID(as_uuid=True), sa.ForeignKey("farben.id"), nullable=True),
        sa.Column("streifenanzahl", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint(
            "farbstandard", "name", "streifenfarbe_id", "streifenanzahl", name="uq_farbe_identitaet"
        ),
    )

    op.create_table(
        "produktfamilien",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("hersteller_id", UUID(as_uuid=True), sa.ForeignKey("hersteller.id"), nullable=False),
        sa.Column("kategorie_id", UUID(as_uuid=True), sa.ForeignKey("produktkategorien.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("beschreibung", sa.Text(), nullable=True),
        sa.Column("quelle_url", sa.String(), nullable=True),
        sa.Column("quelle_version", sa.String(), nullable=True),
        sa.Column("quelle_abgerufen_am", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("geaendert_am", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("hersteller_id", "name", name="uq_produktfamilie_hersteller_name"),
    )
    op.create_index("idx_produktfamilien_hersteller", "produktfamilien", ["hersteller_id"])
    op.create_index("idx_produktfamilien_kategorie", "produktfamilien", ["kategorie_id"])

    op.create_table(
        "produkte",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("produktfamilie_id", UUID(as_uuid=True), sa.ForeignKey("produktfamilien.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("hersteller_artikelnummer", sa.String(), nullable=True),
        sa.Column("produkttyp", sa.String(), nullable=False),
        sa.Column("beschreibung", sa.Text(), nullable=True),
        sa.Column("technische_daten", JSONB(), nullable=True),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("benutzerdefiniert", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("quelle_url", sa.String(), nullable=True),
        sa.Column("quelle_abgerufen_am", sa.DateTime(timezone=True), nullable=True),
        sa.Column("erstellt_von_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("geaendert_am", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("produktfamilie_id", "name", name="uq_produkt_familie_name"),
    )
    op.create_index("idx_produkte_familie", "produkte", ["produktfamilie_id"])
    op.create_index("idx_produkte_typ", "produkte", ["produkttyp"])

    op.create_table(
        "rohrverband_vorlagen",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("produkt_id", UUID(as_uuid=True), sa.ForeignKey("produkte.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("aussenmantel_farbe_id", UUID(as_uuid=True), sa.ForeignKey("farben.id"), nullable=True),
        sa.Column("rohranzahl", sa.Integer(), nullable=False),
        sa.Column("layout_typ", sa.String(), nullable=False, server_default="ring"),
        sa.Column("technische_daten", JSONB(), nullable=True),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_rohrverband_vorlagen_produkt", "rohrverband_vorlagen", ["produkt_id"])

    op.create_table(
        "rohrverband_vorlage_positionen",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("vorlage_id", UUID(as_uuid=True), sa.ForeignKey("rohrverband_vorlagen.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("rohrfarbe_id", UUID(as_uuid=True), sa.ForeignKey("farben.id"), nullable=False),
        sa.Column("streifenfarbe_id", UUID(as_uuid=True), sa.ForeignKey("farben.id"), nullable=True),
        sa.Column("streifenanzahl", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("aussendurchmesser_mm", sa.Float(), nullable=True),
        sa.Column("innendurchmesser_mm", sa.Float(), nullable=True),
        sa.UniqueConstraint("vorlage_id", "position", name="uq_vorlage_position"),
    )
    op.create_index("idx_rvvp_vorlage", "rohrverband_vorlage_positionen", ["vorlage_id"])

    op.create_table(
        "kabel_vorlagen",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("produkt_id", UUID(as_uuid=True), sa.ForeignKey("produkte.id"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("mantelfarbe_id", UUID(as_uuid=True), sa.ForeignKey("farben.id"), nullable=True),
        sa.Column("faseranzahl", sa.Integer(), nullable=True),
        sa.Column("buendeladeranzahl", sa.Integer(), nullable=True),
        sa.Column("kabeldurchmesser_mm", sa.Float(), nullable=True),
        sa.Column("kabeltyp", sa.String(), nullable=False, server_default="glasfaser"),
        sa.Column("faserstandard", sa.String(), nullable=True),
        sa.Column("technische_daten", JSONB(), nullable=True),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_kabel_vorlagen_produkt", "kabel_vorlagen", ["produkt_id"])


def downgrade() -> None:
    op.drop_table("kabel_vorlagen")
    op.drop_table("rohrverband_vorlage_positionen")
    op.drop_table("rohrverband_vorlagen")
    op.drop_table("produkte")
    op.drop_table("produktfamilien")
    op.drop_table("farben")
    op.drop_table("produktkategorien")
    op.drop_table("hersteller")

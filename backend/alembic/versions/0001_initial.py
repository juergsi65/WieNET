"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import geoalchemy2

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String, unique=True, nullable=False, index=True),
        sa.Column("full_name", sa.String, nullable=False),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("role", sa.Enum("admin", "planer", "techniker", "betrachter", name="userrole"), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "bauabschnitte",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("status", sa.Enum("geplant", "aktiv", "stillgelegt", "gestoert", name="objektstatus"), nullable=False),
        sa.Column("geplant_von", sa.DateTime(timezone=True)),
        sa.Column("geplant_bis", sa.DateTime(timezone=True)),
        sa.Column("notizen", sa.Text),
    )

    op.create_table(
        "trassen",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("typ", sa.String),
        sa.Column("status", sa.Enum("geplant", "aktiv", "stillgelegt", "gestoert", name="objektstatus"), nullable=False),
        sa.Column("verlegetiefe_cm", sa.Integer),
        sa.Column("oberflaeche", sa.String),
        sa.Column("laenge_m", sa.Float),
        sa.Column("geometrie", geoalchemy2.Geometry(geometry_type="LINESTRING", srid=4326), nullable=False),
        sa.Column("bauabschnitt_id", UUID(as_uuid=True), sa.ForeignKey("bauabschnitte.id")),
        sa.Column("notizen", sa.Text),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("aktualisiert_am", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "rohrverbaende",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("trasse_id", UUID(as_uuid=True), sa.ForeignKey("trassen.id"), nullable=False),
        sa.Column("bezeichnung", sa.String, nullable=False),
    )

    op.create_table(
        "rohre",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rohrverband_id", UUID(as_uuid=True), sa.ForeignKey("rohrverbaende.id"), nullable=False),
        sa.Column("nummer", sa.Integer, nullable=False),
        sa.Column("farbe", sa.String, nullable=False),
        sa.Column("durchmesser_mm", sa.Float),
        sa.Column("typ", sa.String),
        sa.Column("status", sa.Enum("frei", "belegt", "reserviert", "blockiert", "beschaedigt", name="rohrstatus"), nullable=False),
    )

    op.create_table(
        "netzelemente",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("typ", sa.Enum(
            "olt", "pon", "splitter", "pop", "fcp", "verteiler", "muffe", "schacht",
            "kasten", "hausanschluss", "gebaeude", "technikstandort", name="netzelementtyp"
        ), nullable=False),
        sa.Column("status", sa.Enum("geplant", "aktiv", "stillgelegt", "gestoert", name="objektstatus"), nullable=False),
        sa.Column("geometrie", geoalchemy2.Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("adresse", sa.String),
        sa.Column("gemeinde", sa.String),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("netzelemente.id")),
        sa.Column("ports_gesamt", sa.Integer),
        sa.Column("ports_belegt", sa.Integer, default=0),
        sa.Column("baujahr", sa.Integer),
        sa.Column("betreiber", sa.String),
        sa.Column("eigentuemer", sa.String),
        sa.Column("hersteller", sa.String),
        sa.Column("modell", sa.String),
        sa.Column("notizen", sa.Text),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "kabel",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("bezeichnung", sa.String, nullable=False),
        sa.Column("typ", sa.Enum("glasfaser", "kupfer", name="kabeltyp"), nullable=False),
        sa.Column("fasernanzahl", sa.Integer),
        sa.Column("belegte_fasern", sa.Integer, default=0),
        sa.Column("laenge_m", sa.Float),
        sa.Column("hersteller", sa.String),
        sa.Column("status", sa.Enum("geplant", "aktiv", "stillgelegt", "gestoert", name="objektstatus"), nullable=False),
        sa.Column("fremdfaser", sa.Boolean, default=False),
        sa.Column("reservekabel", sa.Boolean, default=False),
        sa.Column("geometrie", geoalchemy2.Geometry(geometry_type="LINESTRING", srid=4326)),
        sa.Column("kabelanfang_id", UUID(as_uuid=True), sa.ForeignKey("netzelemente.id")),
        sa.Column("kabelende_id", UUID(as_uuid=True), sa.ForeignKey("netzelemente.id")),
    )

    op.create_table(
        "rohr_kabel_belegung",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rohr_id", UUID(as_uuid=True), sa.ForeignKey("rohre.id"), nullable=False),
        sa.Column("kabel_id", UUID(as_uuid=True), sa.ForeignKey("kabel.id"), nullable=False),
        sa.Column("segment_start_m", sa.Float, default=0),
        sa.Column("segment_ende_m", sa.Float),
    )

    op.create_table(
        "stoerungen",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("titel", sa.String, nullable=False),
        sa.Column("beschreibung", sa.Text),
        sa.Column("objekt_typ", sa.String),
        sa.Column("objekt_id", UUID(as_uuid=True)),
        sa.Column("offen", sa.Boolean, default=True),
        sa.Column("gemeldet_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("behoben_am", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("aktion", sa.String, nullable=False),
        sa.Column("objekt_typ", sa.String, nullable=False),
        sa.Column("objekt_id", UUID(as_uuid=True)),
        sa.Column("details", sa.Text),
        sa.Column("zeitpunkt", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("idx_trassen_geom", "trassen", ["geometrie"], postgresql_using="gist")
    op.create_index("idx_netzelemente_geom", "netzelemente", ["geometrie"], postgresql_using="gist")
    op.create_index("idx_kabel_geom", "kabel", ["geometrie"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("stoerungen")
    op.drop_table("rohr_kabel_belegung")
    op.drop_table("kabel")
    op.drop_table("netzelemente")
    op.drop_table("rohre")
    op.drop_table("rohrverbaende")
    op.drop_table("trassen")
    op.drop_table("bauabschnitte")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS objektstatus")
    op.execute("DROP TYPE IF EXISTS rohrstatus")
    op.execute("DROP TYPE IF EXISTS netzelementtyp")
    op.execute("DROP TYPE IF EXISTS kabeltyp")

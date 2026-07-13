"""Nummernvergabe-System + fehlende Gebiet-/Cluster-Felder

Rein additiv: neue nullable Spalten auf areas/clusters, drei neue Tabellen.
Kein bestehender Datensatz wird verändert; ohne konfiguriertes Nummernschema
bleibt gebiete.nummer/clusters.nummer weiterhin frei editierbar wie bisher.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("areas", sa.Column("nummer", sa.String(), nullable=True))
    op.add_column("areas", sa.Column("erstellt_von_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("areas", sa.Column("geaendert_von_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))

    op.add_column("clusters", sa.Column("kuerzel", sa.String(), nullable=True))
    op.add_column("clusters", sa.Column("erstellt_von_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("clusters", sa.Column("geaendert_von_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))

    op.create_table(
        "nummernschemata",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("pattern", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False, server_default="global"),
        sa.Column("start_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("aktiv", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("geaendert_am", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_nummernschema_entity_aktiv ON nummernschemata (entity_type) WHERE aktiv = true"
    )

    op.create_table(
        "nummernkreise",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("schema_id", UUID(as_uuid=True), sa.ForeignKey("nummernschemata.id"), nullable=False),
        sa.Column("scope_key", sa.String(), nullable=False),
        sa.Column("next_value", sa.Integer(), nullable=False),
        sa.UniqueConstraint("schema_id", "scope_key", name="uq_nummernkreis_schema_scope"),
    )

    op.create_table(
        "vergebene_nummern",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("schema_id", UUID(as_uuid=True), sa.ForeignKey("nummernschemata.id"), nullable=False),
        sa.Column("nummer", sa.String(), nullable=False),
        sa.Column("objekt_typ", sa.String(), nullable=False),
        sa.Column("objekt_id", UUID(as_uuid=True), nullable=True),
        sa.Column("vergeben_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_vergebene_nummern_objekt", "vergebene_nummern", ["objekt_typ", "objekt_id"])


def downgrade() -> None:
    op.drop_index("idx_vergebene_nummern_objekt", table_name="vergebene_nummern")
    op.drop_table("vergebene_nummern")
    op.drop_table("nummernkreise")
    op.execute("DROP INDEX IF EXISTS uq_nummernschema_entity_aktiv")
    op.drop_table("nummernschemata")

    op.drop_column("clusters", "geaendert_von_id")
    op.drop_column("clusters", "erstellt_von_id")
    op.drop_column("clusters", "kuerzel")

    op.drop_column("areas", "geaendert_von_id")
    op.drop_column("areas", "erstellt_von_id")
    op.drop_column("areas", "nummer")

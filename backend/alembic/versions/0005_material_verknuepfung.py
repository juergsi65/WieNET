"""Verknüpfung von Rohrverband/Rohr/Kabel mit dem Materialkatalog

Rein additiv: drei neue, nullable Fremdschlüssel-Spalten. Bestehende Rohrverbände/
Rohre/Kabel bleiben unverändert gültig (vorlage_id/farbe_id NULL = "kein Katalog-
Bezug", z.B. weiterhin freier Text bzw. Alt-Hexfarbe in rohre.farbe).

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rohrverbaende", sa.Column("vorlage_id", UUID(as_uuid=True), sa.ForeignKey("rohrverband_vorlagen.id"), nullable=True))
    op.add_column("rohre", sa.Column("farbe_id", UUID(as_uuid=True), sa.ForeignKey("farben.id"), nullable=True))
    op.add_column("kabel", sa.Column("vorlage_id", UUID(as_uuid=True), sa.ForeignKey("kabel_vorlagen.id"), nullable=True))
    op.create_index("idx_rohrverbaende_vorlage", "rohrverbaende", ["vorlage_id"])
    op.create_index("idx_rohre_farbe", "rohre", ["farbe_id"])
    op.create_index("idx_kabel_vorlage", "kabel", ["vorlage_id"])


def downgrade() -> None:
    op.drop_index("idx_kabel_vorlage", table_name="kabel")
    op.drop_index("idx_rohre_farbe", table_name="rohre")
    op.drop_index("idx_rohrverbaende_vorlage", table_name="rohrverbaende")
    op.drop_column("kabel", "vorlage_id")
    op.drop_column("rohre", "farbe_id")
    op.drop_column("rohrverbaende", "vorlage_id")

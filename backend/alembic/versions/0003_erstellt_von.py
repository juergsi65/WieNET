"""erstellt_von_id fuer trassen, kabel, netzelemente

Ermöglicht die klare Unterscheidung zwischen Live-/Echtdaten (Status "aktiv")
und Planungsdaten (Status "geplant"), inklusive Zuordnung zum erfassenden
Benutzer für die Anzeige "Planung von <Benutzername>".

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trassen", sa.Column("erstellt_von_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("kabel", sa.Column("erstellt_von_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("netzelemente", sa.Column("erstellt_von_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.create_index("idx_trassen_erstellt_von", "trassen", ["erstellt_von_id"])
    op.create_index("idx_netzelemente_erstellt_von", "netzelemente", ["erstellt_von_id"])


def downgrade() -> None:
    op.drop_index("idx_netzelemente_erstellt_von", table_name="netzelemente")
    op.drop_index("idx_trassen_erstellt_von", table_name="trassen")
    op.drop_column("netzelemente", "erstellt_von_id")
    op.drop_column("kabel", "erstellt_von_id")
    op.drop_column("trassen", "erstellt_von_id")

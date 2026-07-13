"""audit_logs FKs auf ON DELETE SET NULL umstellen

Bug gefunden beim Testen der neuen Cluster-Lösch-/Merge-Funktionen: Jede Löschung
eines Gebiets/Clusters/Projekts schlug mit einem FK-Verstoß fehl, sobald jemals
ein Audit-Log-Eintrag dafür geschrieben wurde (praktisch immer, da schon das
Anlegen selbst geloggt wird) - die alten FK-Constraints hatten kein ON DELETE
SET NULL. Betrifft nicht nur den neuen Merge, sondern auch den bereits
bestehenden einfachen Cluster-Lösch-Endpunkt.

Rein strukturell additiv im Sinne von "keine Datenverluste": bestehende
Audit-Log-Zeilen bleiben unverändert erhalten, nur das künftige Verhalten bei
Löschung des referenzierten Objekts ändert sich (Referenz wird NULL statt die
Löschung zu blockieren).

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-13

"""
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("audit_logs_area_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key("audit_logs_area_id_fkey", "audit_logs", "areas", ["area_id"], ["id"], ondelete="SET NULL")

    op.drop_constraint("audit_logs_cluster_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key("audit_logs_cluster_id_fkey", "audit_logs", "clusters", ["cluster_id"], ["id"], ondelete="SET NULL")

    op.drop_constraint("audit_logs_project_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key("audit_logs_project_id_fkey", "audit_logs", "projects", ["project_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("audit_logs_project_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key("audit_logs_project_id_fkey", "audit_logs", "projects", ["project_id"], ["id"])

    op.drop_constraint("audit_logs_cluster_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key("audit_logs_cluster_id_fkey", "audit_logs", "clusters", ["cluster_id"], ["id"])

    op.drop_constraint("audit_logs_area_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key("audit_logs_area_id_fkey", "audit_logs", "areas", ["area_id"], ["id"])

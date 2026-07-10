"""admin, areas, clusters, projects, permissions, audit log v2

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import geoalchemy2

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- User-Tabelle erweitern ---
    op.add_column("users", sa.Column("username", sa.String, unique=True, nullable=True))
    op.add_column("users", sa.Column("vorname", sa.String, nullable=True))
    op.add_column("users", sa.Column("nachname", sa.String, nullable=True))
    op.add_column("users", sa.Column("abteilung", sa.String, nullable=True))
    op.add_column("users", sa.Column("firma", sa.String, nullable=True))
    op.add_column("users", sa.Column("telefon", sa.String, nullable=True))
    op.add_column("users", sa.Column("notiz", sa.String, nullable=True))
    op.add_column("users", sa.Column("muss_passwort_aendern", sa.Boolean, server_default="false"))
    op.add_column("users", sa.Column("ablauf_datum", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("letzter_login", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("fehlgeschlagene_logins", sa.Integer, server_default="0"))
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'projektleiter'")

    # --- areas ---
    op.create_table(
        "areas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("kuerzel", sa.String),
        sa.Column("beschreibung", sa.Text),
        sa.Column("gebietstyp", sa.String),
        sa.Column("status", sa.Enum("aktiv", "inaktiv", "archiviert", name="gebietstatus"), nullable=False),
        sa.Column("geometrie", geoalchemy2.Geometry(geometry_type="MULTIPOLYGON", srid=4326)),
        sa.Column("flaeche_m2", sa.Float),
        sa.Column("betreiber", sa.String),
        sa.Column("eigentuemer", sa.String),
        sa.Column("organisation", sa.String),
        sa.Column("ansprechpartner", sa.String),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("areas.id")),
        sa.Column("farbe", sa.String),
        sa.Column("notizen", sa.Text),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("geaendert_am", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_areas_geom", "areas", ["geometrie"], postgresql_using="gist")

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("projektnummer", sa.String),
        sa.Column("projektcode", sa.String, index=True),
        sa.Column("beschreibung", sa.Text),
        sa.Column("status", sa.Enum(
            "entwurf", "planung", "genehmigung", "ausschreibung", "bauvorbereitung", "bau",
            "dokumentation", "abnahme", "betrieb", "pausiert", "abgeschlossen", "storniert", "archiviert",
            name="projektstatus"
        ), nullable=False),
        sa.Column("projektart", sa.String),
        sa.Column("auftraggeber", sa.String),
        sa.Column("betreiber", sa.String),
        sa.Column("eigentuemer", sa.String),
        sa.Column("projektleiter_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("planer_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("baufirma", sa.String),
        sa.Column("ansprechpartner", sa.String),
        sa.Column("start_datum", sa.DateTime(timezone=True)),
        sa.Column("geplantes_ende", sa.DateTime(timezone=True)),
        sa.Column("tatsaechliches_ende", sa.DateTime(timezone=True)),
        sa.Column("budget", sa.Float),
        sa.Column("kostenstand", sa.Float),
        sa.Column("fortschritt_pct", sa.Integer, server_default="0"),
        sa.Column("notizen", sa.Text),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("geaendert_am", sa.DateTime(timezone=True)),
    )

    # --- clusters ---
    op.create_table(
        "clusters",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("nummer", sa.String),
        sa.Column("beschreibung", sa.Text),
        sa.Column("typ", sa.String),
        sa.Column("status", sa.Enum(
            "geplant", "aktiv", "im_bau", "abgeschlossen", "pausiert", "archiviert", name="clusterstatus"
        ), nullable=False),
        sa.Column("geometrie", geoalchemy2.Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False),
        sa.Column("flaeche_m2", sa.Float),
        sa.Column("farbe", sa.String),
        sa.Column("prioritaet", sa.Integer, server_default="3"),
        sa.Column("gebiet_id", UUID(as_uuid=True), sa.ForeignKey("areas.id")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("projektleiter_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("planer_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("baufirma", sa.String),
        sa.Column("start_datum", sa.DateTime(timezone=True)),
        sa.Column("geplantes_ende", sa.DateTime(timezone=True)),
        sa.Column("tatsaechliches_ende", sa.DateTime(timezone=True)),
        sa.Column("budget", sa.Float),
        sa.Column("ausbauziel", sa.Integer),
        sa.Column("anzahl_geplante_anschluesse", sa.Integer, server_default="0"),
        sa.Column("anzahl_aktive_anschluesse", sa.Integer, server_default="0"),
        sa.Column("notizen", sa.Text),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("geaendert_am", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_clusters_geom", "clusters", ["geometrie"], postgresql_using="gist")

    # --- construction_sections (Teilprojekte/Bauabschnitte) ---
    op.create_table(
        "construction_sections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("nummer", sa.Integer),
        sa.Column("beschreibung", sa.Text),
        sa.Column("status", sa.Enum("geplant", "aktiv", "abgeschlossen", "pausiert", name="bauabschnittstatus"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("cluster_id", UUID(as_uuid=True), sa.ForeignKey("clusters.id")),
        sa.Column("verantwortlicher_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("start_datum", sa.DateTime(timezone=True)),
        sa.Column("ende_datum", sa.DateTime(timezone=True)),
        sa.Column("fortschritt_pct", sa.Integer, server_default="0"),
        sa.Column("notizen", sa.Text),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Hauptcluster-Referenz an bestehenden Objekten ---
    op.add_column("trassen", sa.Column("cluster_id", UUID(as_uuid=True), sa.ForeignKey("clusters.id"), nullable=True))
    op.add_column("netzelemente", sa.Column("cluster_id", UUID(as_uuid=True), sa.ForeignKey("clusters.id"), nullable=True))
    op.create_index("idx_trassen_cluster", "trassen", ["cluster_id"])
    op.create_index("idx_netzelemente_cluster", "netzelemente", ["cluster_id"])

    # --- Objektzuordnungen (zusätzliche/schneidende Cluster, Projektzuordnung) ---
    op.create_table(
        "object_cluster_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("objekt_typ", sa.String, nullable=False),
        sa.Column("objekt_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("cluster_id", UUID(as_uuid=True), sa.ForeignKey("clusters.id"), nullable=False, index=True),
        sa.Column("relation", sa.Enum("enthalten", "schneidet", name="zuordnungsrelation"), nullable=False),
        sa.Column("ist_hauptcluster", sa.Boolean, server_default="true"),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "object_project_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("objekt_typ", sa.String, nullable=False),
        sa.Column("objekt_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("erstellt_am", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Granulare Berechtigungen ---
    permission_enum = sa.Enum(
        "daten_anzeigen", "daten_erstellen", "daten_bearbeiten", "daten_loeschen",
        "fotos_hochladen", "dokumente_hochladen", "import_durchfuehren", "export_durchfuehren",
        "berichte_erstellen", "projekte_erstellen", "projekte_bearbeiten", "cluster_erstellen",
        "cluster_bearbeiten", "benutzer_verwalten", "rollen_verwalten", "audit_log_anzeigen",
        "systemeinstellungen_aendern", "backups_erstellen", "backups_wiederherstellen",
        name="permission",
    )

    op.create_table(
        "user_area_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("area_id", UUID(as_uuid=True), sa.ForeignKey("areas.id"), nullable=False, index=True),
        sa.Column("permission", permission_enum, nullable=False),
    )
    op.create_table(
        "user_cluster_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("cluster_id", UUID(as_uuid=True), sa.ForeignKey("clusters.id"), nullable=False, index=True),
        sa.Column("permission", permission_enum, nullable=False),
    )
    op.create_table(
        "user_project_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("permission", permission_enum, nullable=False),
    )

    # --- Erweitertes Audit-Log ---
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("zeitpunkt", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column("aktion", sa.String, nullable=False),
        sa.Column("objekt_typ", sa.String),
        sa.Column("objekt_id", UUID(as_uuid=True)),
        sa.Column("alter_wert", sa.Text),
        sa.Column("neuer_wert", sa.Text),
        sa.Column("area_id", UUID(as_uuid=True), sa.ForeignKey("areas.id")),
        sa.Column("cluster_id", UUID(as_uuid=True), sa.ForeignKey("clusters.id")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("ip_adresse", sa.String),
        sa.Column("ergebnis", sa.Enum("erfolg", "fehler", "verweigert", name="auditergebnis"), server_default="erfolg"),
        sa.Column("fehlerbeschreibung", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("user_project_permissions")
    op.drop_table("user_cluster_permissions")
    op.drop_table("user_area_permissions")
    op.drop_table("object_project_assignments")
    op.drop_table("object_cluster_assignments")
    op.drop_index("idx_netzelemente_cluster", table_name="netzelemente")
    op.drop_index("idx_trassen_cluster", table_name="trassen")
    op.drop_column("netzelemente", "cluster_id")
    op.drop_column("trassen", "cluster_id")
    op.drop_table("construction_sections")
    op.drop_table("clusters")
    op.drop_table("projects")
    op.drop_table("areas")

    for col in ["fehlgeschlagene_logins", "letzter_login", "ablauf_datum", "muss_passwort_aendern",
                "notiz", "telefon", "firma", "abteilung", "nachname", "vorname", "username"]:
        op.drop_column("users", col)

    op.execute("DROP TYPE IF EXISTS permission")
    op.execute("DROP TYPE IF EXISTS auditergebnis")
    op.execute("DROP TYPE IF EXISTS zuordnungsrelation")
    op.execute("DROP TYPE IF EXISTS bauabschnittstatus")
    op.execute("DROP TYPE IF EXISTS clusterstatus")
    op.execute("DROP TYPE IF EXISTS projektstatus")
    op.execute("DROP TYPE IF EXISTS gebietstatus")

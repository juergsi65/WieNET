import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { adminAreaApi, adminClusterApi, adminProjectApi, adminUserApi, adminSystemApi } from "../../lib/api";

export default function AdminOverview() {
  const [counts, setCounts] = useState({ areas: 0, clusters: 0, projects: 0, users: 0 });
  const [status, setStatus] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([adminAreaApi.list(), adminClusterApi.list({ with_geometry: false }), adminProjectApi.list(), adminUserApi.list()])
      .then(([areas, clusters, projects, users]) => {
        setCounts({
          areas: areas.data.length, clusters: clusters.data.length,
          projects: projects.data.length, users: users.data.length,
        });
      });
    adminSystemApi.status().then((res) => setStatus(res.data)).catch(() => {});
  }, []);

  const cards = [
    { label: "Gebiete", value: counts.areas, path: "gebiete" },
    { label: "Cluster", value: counts.clusters, path: "cluster" },
    { label: "Projekte", value: counts.projects, path: "projekte" },
    { label: "Benutzer", value: counts.users, path: "benutzer" },
  ];

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 mb-1">Administration – Übersicht</h2>
      <p className="text-sm text-slate-500 mb-6">Zentrale Verwaltung von Gebieten, Clustern, Projekten und Benutzern.</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {cards.map((c) => (
          <button
            key={c.path}
            onClick={() => navigate(c.path)}
            className="text-left bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 hover:border-brand-400 transition"
          >
            <p className="text-xs text-slate-400 uppercase tracking-wide">{c.label}</p>
            <p className="text-2xl font-semibold text-slate-800 dark:text-slate-100 mt-1">{c.value}</p>
          </button>
        ))}
      </div>

      {status && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
          <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">Systemstatus (Kurzübersicht)</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div><span className="text-slate-400">Datenbank</span><br />
              <span className={status.datenbank === "ok" ? "text-green-600" : "text-red-600"}>{status.datenbank}</span>
            </div>
            <div><span className="text-slate-400">Version</span><br />{status.version}</div>
            <div><span className="text-slate-400">DB-Größe</span><br />{status.datenbankgroesse ?? "–"}</div>
            <div><span className="text-slate-400">Aktive Benutzer</span><br />{status.anzahl_aktive_benutzer}</div>
          </div>
          <button onClick={() => navigate("systemstatus")} className="text-xs text-brand-600 mt-3 hover:underline">
            Vollständigen Systemstatus anzeigen →
          </button>
        </div>
      )}
    </div>
  );
}

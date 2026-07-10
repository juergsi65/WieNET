import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { adminProjectApi } from "../../lib/api";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-3">
      <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
      <p className="text-xl font-semibold text-slate-800 dark:text-slate-100 mt-0.5">{value}</p>
    </div>
  );
}

export default function ProjectDetail() {
  const { projectId } = useParams();
  const [data, setData] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!projectId) return;
    adminProjectApi.dashboard(projectId).then((res) => setData(res.data));
  }, [projectId]);

  if (!data) return <div className="p-6 text-sm text-slate-500">Wird geladen…</div>;
  const p = data.projekt;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">{p.name}</h2>
      <p className="text-sm text-slate-500 mb-6">{p.projektnummer} · {p.status} · Fortschritt {p.fortschritt_pct}%</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="Cluster" value={data.anzahl_cluster} />
        <StatCard label="Bauabschnitte" value={`${data.bauabschnitte_abgeschlossen}/${data.anzahl_bauabschnitte}`} />
        <StatCard label="Trassenlänge" value={`${data.trassenlaenge_m.toFixed(0)} m`} />
        <StatCard label="Hausanschlüsse" value={data.anzahl_hausanschluesse} />
        <StatCard label="Offene Störungen" value={data.offene_stoerungen} />
        <StatCard label="Budget" value={p.budget ? `€${p.budget.toLocaleString()}` : "–"} />
        <StatCard label="Kostenstand" value={p.kostenstand ? `€${p.kostenstand.toLocaleString()}` : "–"} />
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-3">Cluster in diesem Projekt</p>
        <div className="divide-y divide-slate-100 dark:divide-slate-700">
          {data.cluster_liste.map((c: any) => (
            <button key={c.id} onClick={() => navigate(`/admin/cluster/${c.id}`)}
                    className="w-full flex items-center justify-between py-2 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50 px-2 rounded">
              <span className="text-sm text-slate-700 dark:text-slate-200">{c.name}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600">{c.status}</span>
            </button>
          ))}
          {data.cluster_liste.length === 0 && <p className="text-sm text-slate-400 py-2">Noch keine Cluster zugewiesen.</p>}
        </div>
      </div>
    </div>
  );
}

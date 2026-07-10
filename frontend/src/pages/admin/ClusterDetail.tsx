import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { adminClusterApi } from "../../lib/api";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-3">
      <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
      <p className="text-xl font-semibold text-slate-800 dark:text-slate-100 mt-0.5">{value}</p>
    </div>
  );
}

export default function ClusterDetail() {
  const { clusterId } = useParams();
  const [cluster, setCluster] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    if (!clusterId) return;
    adminClusterApi.get(clusterId).then((res) => setCluster(res.data));
    adminClusterApi.stats(clusterId).then((res) => setStats(res.data));
  }, [clusterId]);

  if (!cluster || !stats) return <div className="p-6 text-sm text-slate-500">Wird geladen…</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-1">
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: cluster.farbe }} />
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">{cluster.name}</h2>
        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600">{cluster.status}</span>
      </div>
      <p className="text-sm text-slate-500 mb-6">{cluster.typ} {cluster.nummer && `· ${cluster.nummer}`}</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="Fläche" value={stats.flaeche_m2 ? `${(stats.flaeche_m2 / 10000).toFixed(2)} ha` : "–"} />
        <StatCard label="Trassenlänge" value={`${stats.trassenlaenge_m.toFixed(0)} m`} />
        <StatCard label="Kabellänge" value={`${stats.kabellaenge_m.toFixed(0)} m`} />
        <StatCard label="Rohrbelegung" value={`${stats.rohrbelegung_pct}%`} />
        <StatCard label="Faserauslastung" value={`${stats.faserauslastung_pct}%`} />
        <StatCard label="Schächte" value={stats.anzahl_schaechte} />
        <StatCard label="Muffen" value={stats.anzahl_muffen} />
        <StatCard label="FCPs" value={stats.anzahl_fcp} />
        <StatCard label="Verteiler" value={stats.anzahl_verteiler} />
        <StatCard label="Hausanschlüsse" value={stats.anzahl_hausanschluesse} />
        <StatCard label="Offene Störungen" value={stats.anzahl_stoerungen} />
        <StatCard label="Bauabschnitte offen/fertig" value={`${stats.bauabschnitte_geplant} / ${stats.bauabschnitte_abgeschlossen}`} />
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">Ausbauziel</p>
        <div className="flex items-center gap-3">
          <div className="flex-1 h-3 rounded bg-slate-100 dark:bg-slate-700 overflow-hidden">
            <div
              className="h-full bg-brand-500"
              style={{ width: `${cluster.ausbauziel ? Math.min(100, 100 * cluster.anzahl_aktive_anschluesse / cluster.ausbauziel) : 0}%` }}
            />
          </div>
          <span className="text-sm text-slate-500 whitespace-nowrap">
            {cluster.anzahl_aktive_anschluesse} / {cluster.ausbauziel ?? "–"} aktive Anschlüsse
          </span>
        </div>
      </div>
    </div>
  );
}

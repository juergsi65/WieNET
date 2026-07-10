import { useEffect, useState } from "react";
import { objektApi } from "../lib/api";

interface Stats {
  trassen_laenge_m: number;
  kabel_laenge_m: number;
  anzahl_schaechte: number;
  anzahl_muffen: number;
  anzahl_hausanschluesse: number;
  rohre_frei: number;
  rohre_belegt: number;
  fasern_frei: number;
  fasern_belegt: number;
  offene_stoerungen: number;
  geplante_bauabschnitte: number;
}

function Card({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
      <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${accent ?? "text-slate-800 dark:text-slate-100"}`}>{value}</p>
    </div>
  );
}

export default function DashboardHome() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    objektApi.dashboard().then((res) => setStats(res.data));
  }, []);

  if (!stats) return <div className="p-6 text-sm text-slate-500">Kennzahlen werden geladen…</div>;

  const rohrGesamt = stats.rohre_frei + stats.rohre_belegt;
  const rohrBelegtPct = rohrGesamt ? Math.round((stats.rohre_belegt / rohrGesamt) * 100) : 0;
  const fasernGesamt = stats.fasern_frei + stats.fasern_belegt;
  const fasernBelegtPct = fasernGesamt ? Math.round((stats.fasern_belegt / fasernGesamt) * 100) : 0;

  return (
    <div className="p-6 overflow-y-auto h-full">
      <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 mb-4">Dashboard</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card label="Trassenlänge" value={`${(stats.trassen_laenge_m / 1000).toFixed(2)} km`} />
        <Card label="Kabellänge" value={`${(stats.kabel_laenge_m / 1000).toFixed(2)} km`} />
        <Card label="Schächte" value={stats.anzahl_schaechte} />
        <Card label="Muffen" value={stats.anzahl_muffen} />
        <Card label="Hausanschlüsse" value={stats.anzahl_hausanschluesse} />
        <Card label="Rohrbelegung" value={`${rohrBelegtPct}%`} accent={rohrBelegtPct > 80 ? "text-red-600" : "text-slate-800"} />
        <Card label="Faserbelegung" value={`${fasernBelegtPct}%`} accent={fasernBelegtPct > 80 ? "text-red-600" : "text-slate-800"} />
        <Card label="Offene Störungen" value={stats.offene_stoerungen} accent={stats.offene_stoerungen > 0 ? "text-red-600" : "text-green-600"} />
        <Card label="Geplante Bauabschnitte" value={stats.geplante_bauabschnitte} />
      </div>
    </div>
  );
}

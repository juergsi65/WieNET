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
    <div className="survey-marks bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4">
      <p className="text-xs text-ink-400 uppercase tracking-wide font-medium">{label}</p>
      <p className={`font-display text-2xl font-semibold mt-1 ${accent ?? "text-ink-900 dark:text-slate-100"}`}>{value}</p>
    </div>
  );
}

export default function DashboardHome() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    objektApi.dashboard().then((res) => setStats(res.data));
  }, []);

  if (!stats) return <div className="p-6 text-sm text-ink-400">Kennzahlen werden geladen…</div>;

  const objekteVorhanden =
    stats.anzahl_schaechte + stats.anzahl_muffen + stats.anzahl_hausanschluesse > 0 || stats.trassen_laenge_m > 0;

  const rohrGesamt = stats.rohre_frei + stats.rohre_belegt;
  const rohrBelegtPct = rohrGesamt ? Math.round((stats.rohre_belegt / rohrGesamt) * 100) : 0;
  const fasernGesamt = stats.fasern_frei + stats.fasern_belegt;
  const fasernBelegtPct = fasernGesamt ? Math.round((stats.fasern_belegt / fasernGesamt) * 100) : 0;

  return (
    <div className="p-6 overflow-y-auto h-full">
      <h2 className="font-display text-xl font-semibold text-ink-900 dark:text-slate-100 mb-4">Dashboard</h2>

      {!objekteVorhanden ? (
        <div className="survey-marks border border-dashed border-ink-100 rounded-lg p-8 text-center max-w-md">
          <p className="font-display text-base font-semibold text-ink-900 mb-1">Noch keine Infrastrukturdaten erfasst</p>
          <p className="text-sm text-ink-400">
            Importiere Trassen, Schächte oder Kabel über <span className="font-medium text-ink-600">Import</span>,
            oder lege sie direkt auf der Karte an, sobald die Zeichenfunktionen aktiviert sind.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card label="Trassenlänge" value={`${(stats.trassen_laenge_m / 1000).toFixed(2)} km`} />
          <Card label="Kabellänge" value={`${(stats.kabel_laenge_m / 1000).toFixed(2)} km`} />
          <Card label="Schächte" value={stats.anzahl_schaechte} />
          <Card label="Muffen" value={stats.anzahl_muffen} />
          <Card label="Hausanschlüsse" value={stats.anzahl_hausanschluesse} />
          <Card label="Rohrbelegung" value={`${rohrBelegtPct}%`} accent={rohrBelegtPct > 80 ? "text-conduit-600" : undefined} />
          <Card label="Faserbelegung" value={`${fasernBelegtPct}%`} accent={fasernBelegtPct > 80 ? "text-conduit-600" : undefined} />
          <Card label="Offene Störungen" value={stats.offene_stoerungen} accent={stats.offene_stoerungen > 0 ? "text-conduit-600" : "text-signal-600"} />
          <Card label="Geplante Bauabschnitte" value={stats.geplante_bauabschnitte} />
        </div>
      )}
    </div>
  );
}

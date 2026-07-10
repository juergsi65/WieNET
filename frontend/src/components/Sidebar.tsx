import { useState } from "react";
import { objektApi } from "../lib/api";
import { useAppStore } from "../store/useAppStore";

const LAYERS: { key: string; label: string; color: string }[] = [
  { key: "cluster", label: "Cluster (Flächen)", color: "#f59e0b" },
  { key: "trassen", label: "Trassen", color: "#16a34a" },
  { key: "schacht", label: "Schächte", color: "#334155" },
  { key: "muffe", label: "Muffen", color: "#eab308" },
  { key: "verteiler", label: "Verteiler / FCP", color: "#0ea5e9" },
  { key: "olt", label: "OLT / PON", color: "#7c3aed" },
  { key: "hausanschluss", label: "Hausanschlüsse", color: "#16a34a" },
];

export default function Sidebar({ onSelectSearchResult }: { onSelectSearchResult: (typ: string, id: string, geom: any) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const activeLayers = useAppStore((s) => s.activeLayers);
  const toggleLayer = useAppStore((s) => s.toggleLayer);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim().length < 2) return;
    setSearching(true);
    try {
      const res = await objektApi.search(query.trim());
      setResults(res.data);
    } finally {
      setSearching(false);
    }
  }

  return (
    <aside className="w-72 shrink-0 h-full bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 overflow-y-auto">
      <div className="p-4 border-b border-slate-200 dark:border-slate-700">
        <form onSubmit={handleSearch}>
          <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">Suche</label>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Adresse, Schacht, Muffe, Kabel…"
            className="mt-1 w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </form>
        {searching && <p className="text-xs text-slate-400 mt-2">Suche läuft…</p>}
        {results.length > 0 && (
          <ul className="mt-2 space-y-1 max-h-56 overflow-y-auto">
            {results.map((r) => (
              <li key={r.id}>
                <button
                  onClick={() => onSelectSearchResult(r.typ, r.id, r.geometrie)}
                  className="w-full text-left text-sm px-2 py-1.5 rounded-md hover:bg-brand-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200"
                >
                  <span className="font-medium">{r.name}</span>
                  <span className="text-xs text-slate-400 ml-1">({r.typ})</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="p-4">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Ebenen</p>
        <ul className="space-y-2">
          {LAYERS.map((l) => (
            <li key={l.key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={activeLayers[l.key] ?? true}
                onChange={() => toggleLayer(l.key)}
                className="rounded accent-brand-600"
              />
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: l.color }} />
              <span className="text-sm text-slate-600 dark:text-slate-300">{l.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="p-4 border-t border-slate-200 dark:border-slate-700">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">Legende</p>
        <ul className="text-xs space-y-1.5 text-slate-500 dark:text-slate-400">
          <li className="flex items-center gap-2"><span className="w-4 h-0.5 bg-green-600 inline-block" /> Aktiv (durchgezogen)</li>
          <li className="flex items-center gap-2"><span className="w-4 h-0.5 border-t-2 border-dashed border-slate-500 inline-block" /> Geplant (gestrichelt)</li>
          <li className="flex items-center gap-2"><span className="w-4 h-0.5 bg-slate-300 inline-block" /> Stillgelegt (ausgegraut)</li>
          <li className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-red-600 inline-block" /> Störung</li>
        </ul>
      </div>
    </aside>
  );
}

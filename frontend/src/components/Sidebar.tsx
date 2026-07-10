import { useEffect, useRef, useState } from "react";
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
  const [activeIndex, setActiveIndex] = useState(-1);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const activeLayers = useAppStore((s) => s.activeLayers);
  const toggleLayer = useAppStore((s) => s.toggleLayer);
  const datenFilter = useAppStore((s) => s.datenFilter);
  const setDatenFilter = useAppStore((s) => s.setDatenFilter);

  // Debounced Live-Suche ab 2 Zeichen
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setResults([]);
      setSearching(false);
      return;
    }
    setSearching(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await objektApi.search(query.trim());
        setResults(res.data);
        setActiveIndex(-1);
      } finally {
        setSearching(false);
      }
    }, 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query]);

  // Globales Tastaturkürzel: "/" fokussiert die Suche (wie in vielen Profi-Tools üblich)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "/" && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function handleSelect(r: any) {
    onSelectSearchResult(r.typ, r.id, r.geometrie);
    setResults([]);
    setQuery("");
    setActiveIndex(-1);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && activeIndex >= 0) {
      e.preventDefault();
      handleSelect(results[activeIndex]);
    } else if (e.key === "Escape") {
      setResults([]);
      setActiveIndex(-1);
      searchInputRef.current?.blur();
    }
  }

  return (
    <aside className="w-72 shrink-0 h-full bg-white dark:bg-slate-800 border-r border-ink-100 dark:border-slate-700 overflow-y-auto">
      <div className="p-4 border-b border-ink-100 dark:border-slate-700">
        <p className="text-xs font-medium text-ink-400 uppercase tracking-wide mb-2">Datenstand</p>
        <div className="grid grid-cols-3 gap-1 text-xs">
          {([
            { key: "alle", label: "Alle" },
            { key: "live", label: "Live" },
            { key: "planung", label: "Planung" },
          ] as const).map((f) => (
            <button
              key={f.key}
              onClick={() => setDatenFilter(f.key)}
              className={`py-1.5 rounded-md font-medium transition-colors duration-150 ${
                datenFilter === f.key
                  ? f.key === "planung" ? "bg-conduit-500 text-white" : f.key === "live" ? "bg-signal-600 text-white" : "bg-ink-900 text-white"
                  : "bg-paper-dim dark:bg-slate-700 text-ink-500 hover:bg-ink-100"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 border-b border-ink-100 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <label className="text-xs font-medium text-ink-400 uppercase tracking-wide">Suche</label>
          <kbd className="text-[10px] text-ink-400 bg-paper-dim dark:bg-slate-700 rounded px-1.5 py-0.5 font-data">/</kbd>
        </div>
        <div className="relative mt-1">
          <input
            ref={searchInputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Adresse, Schacht, Muffe, Kabel…"
            className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-conduit-500 focus:border-conduit-500 transition"
          />
          {searching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 border-2 border-ink-100 border-t-conduit-500 rounded-full animate-spin" />
          )}
        </div>

        {results.length > 0 && (
          <ul className="mt-2 space-y-0.5 max-h-64 overflow-y-auto animate-fade-in">
            {results.map((r, i) => (
              <li key={r.id}>
                <button
                  onClick={() => handleSelect(r)}
                  onMouseEnter={() => setActiveIndex(i)}
                  className={`w-full text-left text-sm px-2 py-1.5 rounded-md transition-colors duration-100 ${
                    i === activeIndex ? "bg-conduit-50 dark:bg-slate-700" : "hover:bg-conduit-50 dark:hover:bg-slate-700"
                  } text-ink-600 dark:text-slate-200`}
                >
                  <span className="font-medium">{r.name}</span>
                  <span className="text-xs text-ink-400 ml-1">({r.typ})</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {!searching && query.trim().length >= 2 && results.length === 0 && (
          <p className="text-xs text-ink-400 mt-2">Keine Treffer für „{query}“.</p>
        )}
      </div>

      <div className="p-4">
        <p className="text-xs font-medium text-ink-400 uppercase tracking-wide mb-2">Ebenen</p>
        <ul className="space-y-2">
          {LAYERS.map((l) => (
            <li key={l.key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={activeLayers[l.key] ?? true}
                onChange={() => toggleLayer(l.key)}
                className="rounded accent-conduit-600"
              />
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: l.color }} />
              <span className="text-sm text-ink-600 dark:text-slate-300">{l.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="p-4 border-t border-ink-100 dark:border-slate-700">
        <p className="text-xs font-medium text-ink-400 uppercase tracking-wide mb-2">Legende</p>
        <ul className="text-xs space-y-1.5 text-ink-400 dark:text-slate-400">
          <li className="flex items-center gap-2"><span className="w-4 h-0.5 bg-signal-600 inline-block" /> Live-Daten / aktiv (durchgezogen, grün)</li>
          <li className="flex items-center gap-2"><span className="w-4 h-0.5 border-t-2 border-dashed border-conduit-500 inline-block" /> Planung (gestrichelt, orange)</li>
          <li className="flex items-center gap-2"><span className="w-4 h-0.5 bg-slate-300 inline-block" /> Stillgelegt (ausgegraut)</li>
          <li className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-conduit-600 inline-block" /> Störung</li>
        </ul>
      </div>
    </aside>
  );
}

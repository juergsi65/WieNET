import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { adminProjectApi } from "../../lib/api";

interface Project {
  id: string; name: string; projektnummer: string | null; projektcode: string | null;
  status: string; fortschritt_pct: number; anzahl_cluster: number; budget: number | null;
}

const STATUS_OPTIONEN = [
  "entwurf", "planung", "genehmigung", "ausschreibung", "bauvorbereitung", "bau",
  "dokumentation", "abnahme", "betrieb", "pausiert", "abgeschlossen", "storniert", "archiviert",
];

const STATUS_FARBE: Record<string, string> = {
  bau: "bg-blue-100 text-blue-700", betrieb: "bg-green-100 text-green-700",
  abgeschlossen: "bg-slate-200 text-slate-600", storniert: "bg-red-100 text-red-700",
  pausiert: "bg-amber-100 text-amber-700",
};

export default function ProjectManagement() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", projektnummer: "", projektcode: "", status: "entwurf",
    projektart: "FTTH-Ausbau", auftraggeber: "", budget: "",
  });
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  function load() {
    adminProjectApi.list().then((res) => setProjects(res.data));
  }
  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await adminProjectApi.create({ ...form, budget: form.budget ? Number(form.budget) : null });
      setShowForm(false);
      setForm({ name: "", projektnummer: "", projektcode: "", status: "entwurf", projektart: "FTTH-Ausbau", auftraggeber: "", budget: "" });
      load();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Projekt konnte nicht angelegt werden.");
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">Projekte</h2>
          <p className="text-sm text-slate-500">Enthält mehrere Gebiete, Cluster, Teilprojekte und Bauabschnitte.</p>
        </div>
        <button onClick={() => setShowForm((v) => !v)} className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">
          {showForm ? "Abbrechen" : "+ Neues Projekt"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 mb-6 grid grid-cols-2 gap-3">
          {error && <p className="col-span-2 text-sm text-red-600">{error}</p>}
          <input required placeholder="Projektname" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
          <input placeholder="Projektnummer" value={form.projektnummer} onChange={(e) => setForm({ ...form, projektnummer: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
          <input placeholder="Projektcode" value={form.projektcode} onChange={(e) => setForm({ ...form, projektcode: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
            {STATUS_OPTIONEN.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <input placeholder="Auftraggeber" value={form.auftraggeber} onChange={(e) => setForm({ ...form, auftraggeber: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
          <input type="number" placeholder="Budget (€)" value={form.budget} onChange={(e) => setForm({ ...form, budget: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
          <button type="submit" className="col-span-2 bg-brand-600 text-white rounded-lg py-2 text-sm font-medium">Projekt speichern</button>
        </form>
      )}

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {projects.map((p) => (
          <button key={p.id} onClick={() => navigate(p.id)}
                  className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50">
            <div>
              <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{p.name} {p.projektnummer && <span className="text-slate-400 font-normal">({p.projektnummer})</span>}</p>
              <p className="text-xs text-slate-400">{p.anzahl_cluster} Cluster · Fortschritt {p.fortschritt_pct}% {p.budget ? `· Budget €${p.budget.toLocaleString()}` : ""}</p>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_FARBE[p.status] ?? "bg-slate-100 text-slate-600"}`}>{p.status}</span>
          </button>
        ))}
        {projects.length === 0 && <p className="p-4 text-sm text-slate-400">Noch keine Projekte angelegt.</p>}
      </div>
    </div>
  );
}

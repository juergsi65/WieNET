import { useEffect, useState } from "react";
import { adminAreaApi } from "../../lib/api";
import PolygonDrawMap from "../../components/PolygonDrawMap";
import { toast } from "../../store/useToastStore";

interface Area {
  id: string; name: string; kuerzel: string | null; gebietstyp: string | null;
  status: string; flaeche_m2: number | null; anzahl_cluster: number; farbe: string;
}

export default function AreaManagement() {
  const [areas, setAreas] = useState<Area[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const [geometrie, setGeometrie] = useState<any>(null);
  const [flaeche, setFlaeche] = useState<number | null>(null);
  const [form, setForm] = useState({ name: "", kuerzel: "", gebietstyp: "Ausbaugebiet", farbe: "#0ea5e9", beschreibung: "" });
  const [error, setError] = useState<string | null>(null);

  function load() {
    adminAreaApi.list().then((res) => setAreas(res.data));
  }
  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await adminAreaApi.create({ ...form, geometrie });
      setShowForm(false);
      setGeometrie(null);
      setForm({ name: "", kuerzel: "", gebietstyp: "Ausbaugebiet", farbe: "#0ea5e9", beschreibung: "" });
      load();
      toast.success(`Gebiet "${form.name}" wurde angelegt.`);
    } catch (e: any) {
      const msg = e.response?.data?.detail ?? "Gebiet konnte nicht angelegt werden.";
      setError(msg);
      toast.error(msg);
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100">Gebiete</h2>
          <p className="text-sm text-slate-500">Oberste räumliche Organisationseinheit (Bundesland, Gemeinde, Ausbaugebiet, …)</p>
        </div>
        <button onClick={() => setShowForm((v) => !v)} className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">
          {showForm ? "Abbrechen" : "+ Neues Gebiet"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 mb-6 space-y-3">
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <input required placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                   className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
            <input placeholder="Kürzel" value={form.kuerzel} onChange={(e) => setForm({ ...form, kuerzel: e.target.value })}
                   className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
            <select value={form.gebietstyp} onChange={(e) => setForm({ ...form, gebietstyp: e.target.value })}
                    className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              {["Bundesland", "Bezirk", "Gemeinde", "Katastralgemeinde", "Versorgungsgebiet", "Ausbaugebiet", "Betreibergebiet"].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <input type="color" value={form.farbe} onChange={(e) => setForm({ ...form, farbe: e.target.value })}
                   className="rounded-lg border border-slate-300 dark:border-slate-600 h-10" />
          </div>
          <textarea placeholder="Beschreibung" value={form.beschreibung} onChange={(e) => setForm({ ...form, beschreibung: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" rows={2} />

          <div>
            {!showMap && !geometrie && (
              <button type="button" onClick={() => setShowMap(true)} className="text-sm text-brand-600 hover:underline">
                Optional: Gebietsgrenze auf Karte zeichnen
              </button>
            )}
            {geometrie && !showMap && (
              <p className="text-sm text-green-600">
                Polygon erfasst ({flaeche ? (flaeche / 10000).toFixed(2) : "?"} ha).{" "}
                <button type="button" onClick={() => setShowMap(true)} className="text-brand-600 hover:underline">Neu zeichnen</button>
              </p>
            )}
            {showMap && (
              <div className="h-96 rounded-lg overflow-hidden border border-ink-100 dark:border-slate-700 mt-2">
                <PolygonDrawMap
                  onComplete={(geo, fl) => { setGeometrie(geo); setFlaeche(fl); setShowMap(false); }}
                />
              </div>
            )}
          </div>

          <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">Gebiet speichern</button>
        </form>
      )}

      <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {areas.map((a) => (
          <div key={a.id} className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: a.farbe }} />
              <div>
                <p className="text-sm font-medium text-ink-900 dark:text-slate-100">{a.name} {a.kuerzel && <span className="text-ink-400 font-normal">({a.kuerzel})</span>}</p>
                <p className="text-xs text-slate-400">{a.gebietstyp} · {a.anzahl_cluster} Cluster {a.flaeche_m2 ? `· ${(a.flaeche_m2 / 10000).toFixed(1)} ha` : ""}</p>
              </div>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{a.status}</span>
          </div>
        ))}
        {areas.length === 0 && <p className="p-4 text-sm text-slate-400">Noch keine Gebiete angelegt.</p>}
      </div>
    </div>
  );
}

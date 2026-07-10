import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { adminClusterApi, adminAreaApi, adminProjectApi } from "../../lib/api";
import PolygonDrawMap from "../../components/PolygonDrawMap";

interface Cluster {
  id: string; name: string; nummer: string | null; typ: string | null; status: string;
  farbe: string; flaeche_m2: number | null; gebiet_id: string | null; project_id: string | null;
}

const TYPEN = ["FTTH-Ausbaucluster", "PON-Cluster", "FCP-Versorgungsbereich", "Baucluster", "Wohngebiet", "Gewerbegebiet", "Störungsgebiet", "Wartungsbereich"];

export default function ClusterManagement() {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [areas, setAreas] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [step, setStep] = useState<"liste" | "zeichnen" | "formular" | "zuordnung">("liste");
  const [geometrie, setGeometrie] = useState<any>(null);
  const [flaeche, setFlaeche] = useState(0);
  const [form, setForm] = useState({ name: "", nummer: "", typ: "Baucluster", farbe: "#f59e0b", gebiet_id: "", project_id: "" });
  const [neuerClusterId, setNeuerClusterId] = useState<string | null>(null);
  const [vorschau, setVorschau] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  function load() {
    adminClusterApi.list({ with_geometry: false }).then((res) => setClusters(res.data));
  }
  useEffect(() => {
    load();
    adminAreaApi.list().then((res) => setAreas(res.data));
    adminProjectApi.list().then((res) => setProjects(res.data));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await adminClusterApi.create({
        ...form,
        gebiet_id: form.gebiet_id || null,
        project_id: form.project_id || null,
        geometrie,
      });
      setNeuerClusterId(res.data.id);
      const vorschauRes = await adminClusterApi.zuordnungVorschau(res.data.id);
      setVorschau(vorschauRes.data);
      setStep("zuordnung");
      load();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Cluster konnte nicht angelegt werden.");
    }
  }

  async function handleZuordnungBestaetigen(typen: string[]) {
    if (!neuerClusterId) return;
    await adminClusterApi.zuordnungBestaetigen(neuerClusterId, typen);
    resetWizard();
  }

  function resetWizard() {
    setStep("liste");
    setGeometrie(null);
    setForm({ name: "", nummer: "", typ: "Baucluster", farbe: "#f59e0b", gebiet_id: "", project_id: "" });
    setNeuerClusterId(null);
    setVorschau([]);
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100">Cluster</h2>
          <p className="text-sm text-slate-500">Räumlich/technisch zusammengehörige Ausbau-, Bau- oder Versorgungsbereiche.</p>
        </div>
        {step === "liste" && (
          <button onClick={() => setStep("zeichnen")} className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">
            + Neuer Cluster
          </button>
        )}
        {step !== "liste" && (
          <button onClick={resetWizard} className="text-sm text-ink-400 hover:text-slate-700">Abbrechen</button>
        )}
      </div>

      {step === "zeichnen" && (
        <div>
          <p className="text-sm text-ink-400 mb-2">Schritt 1: Cluster-Polygon auf der Karte zeichnen.</p>
          <div className="h-[28rem] rounded-lg overflow-hidden border border-ink-100 dark:border-slate-700">
            <PolygonDrawMap onComplete={(geo, fl) => { setGeometrie(geo); setFlaeche(fl); setStep("formular"); }} />
          </div>
        </div>
      )}

      {step === "formular" && (
        <form onSubmit={handleCreate} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 space-y-3">
          <p className="text-sm text-slate-500">Schritt 2: Cluster-Stammdaten. Fläche: <strong>{(flaeche / 10000).toFixed(2)} ha</strong></p>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="grid grid-cols-2 gap-3">
            <input required placeholder="Clustername" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                   className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
            <input placeholder="Clusternummer" value={form.nummer} onChange={(e) => setForm({ ...form, nummer: e.target.value })}
                   className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
            <select value={form.typ} onChange={(e) => setForm({ ...form, typ: e.target.value })}
                    className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              {TYPEN.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input type="color" value={form.farbe} onChange={(e) => setForm({ ...form, farbe: e.target.value })}
                   className="rounded-lg border border-slate-300 dark:border-slate-600 h-10" />
            <select value={form.gebiet_id} onChange={(e) => setForm({ ...form, gebiet_id: e.target.value })}
                    className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              <option value="">– kein Gebiet –</option>
              {areas.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <select value={form.project_id} onChange={(e) => setForm({ ...form, project_id: e.target.value })}
                    className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              <option value="">– kein Projekt –</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">
            Cluster speichern und Objektzuordnung prüfen
          </button>
        </form>
      )}

      {step === "zuordnung" && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4">
          <p className="text-sm text-ink-400 mb-3">
            Schritt 3: Das System hat folgende Objekte im Clusterpolygon gefunden. Bitte prüfen und übernehmen.
          </p>
          {vorschau.length === 0 && <p className="text-sm text-slate-400">Keine Tiefbau- oder Netzobjekte im Clusterbereich gefunden.</p>}
          <div className="space-y-2 mb-4">
            {vorschau.map((v) => (
              <div key={v.objekt_typ} className="flex items-center justify-between text-sm border border-slate-100 dark:border-slate-700 rounded-lg px-3 py-2">
                <div>
                  <span className="font-medium capitalize">{v.objekt_typ}</span>
                  <span className="text-ink-400 ml-2">{v.anzahl} gefunden</span>
                </div>
                <div className="text-xs text-slate-500">
                  {v.davon_enthalten} vollständig enthalten · {v.davon_schneidend} schneidend
                  {v.davon_bereits_anders_zugeordnet > 0 && (
                    <span className="text-amber-600 ml-2">· {v.davon_bereits_anders_zugeordnet} bereits anders zugeordnet</span>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleZuordnungBestaetigen(vorschau.map((v) => v.objekt_typ))}
              disabled={vorschau.length === 0}
              className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40"
            >
              Zuordnung bestätigen
            </button>
            <button onClick={resetWizard} className="bg-slate-100 dark:bg-slate-700 rounded-lg px-4 py-2 text-sm">
              Ohne Zuordnung übernehmen
            </button>
          </div>
        </div>
      )}

      {step === "liste" && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
          {clusters.map((c) => (
            <button
              key={c.id}
              onClick={() => navigate(c.id)}
              className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50"
            >
              <div className="flex items-center gap-3">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: c.farbe }} />
                <div>
                  <p className="text-sm font-medium text-ink-900 dark:text-slate-100">{c.name} {c.nummer && <span className="text-ink-400 font-normal">({c.nummer})</span>}</p>
                  <p className="text-xs text-slate-400">{c.typ} {c.flaeche_m2 ? `· ${(c.flaeche_m2 / 10000).toFixed(1)} ha` : ""}</p>
                </div>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{c.status}</span>
            </button>
          ))}
          {clusters.length === 0 && <p className="p-4 text-sm text-slate-400">Noch keine Cluster angelegt.</p>}
        </div>
      )}
    </div>
  );
}

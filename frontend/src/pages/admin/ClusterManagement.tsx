import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { adminClusterApi, adminAreaApi, adminProjectApi } from "../../lib/api";
import PolygonDrawMap from "../../components/PolygonDrawMap";
import { toast } from "../../store/useToastStore";
import { confirmDialog } from "../../store/useConfirmStore";

interface Cluster {
  id: string; name: string; nummer: string | null; kuerzel: string | null; typ: string | null; status: string;
  farbe: string; flaeche_m2: number | null; gebiet_id: string | null; project_id: string | null;
}

const TYPEN = ["FTTH-Ausbaucluster", "PON-Cluster", "FCP-Versorgungsbereich", "Baucluster", "Wohngebiet", "Gewerbegebiet", "Störungsgebiet", "Wartungsbereich"];
const STATUS_LABEL: Record<string, string> = {
  geplant: "Geplant", aktiv: "Aktiv", im_bau: "Im Bau", abgeschlossen: "Abgeschlossen",
  pausiert: "Pausiert/deaktiviert", archiviert: "Archiviert",
};

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

  const [editing, setEditing] = useState<Cluster | null>(null);
  const [editForm, setEditForm] = useState({ name: "", kuerzel: "", status: "geplant", gebiet_id: "", project_id: "" });

  const [mergeMode, setMergeMode] = useState(false);
  const [mergeSelection, setMergeSelection] = useState<Set<string>>(new Set());
  const [mergeVorschau, setMergeVorschau] = useState<any | null>(null);
  const [mergeForm, setMergeForm] = useState({ name: "", gebiet_id: "" });

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
      const msg = e.response?.data?.detail ?? "Cluster konnte nicht angelegt werden.";
      setError(msg);
      toast.error(msg);
    }
  }

  async function handleZuordnungBestaetigen(typen: string[]) {
    if (!neuerClusterId) return;
    try {
      const res = await adminClusterApi.zuordnungBestaetigen(neuerClusterId, typen);
      const z = res.data.zusammenfassung;
      const anzahl = Object.values(z).reduce((sum: number, v: any) => sum + (typeof v === "number" ? v : (v.enthalten ?? 0) + (v.schneidend ?? 0)), 0);
      toast.success(`Cluster gespeichert, ${anzahl} Objekte zugeordnet.`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Zuordnung fehlgeschlagen.");
    }
    resetWizard();
  }

  function resetWizard() {
    setStep("liste");
    setGeometrie(null);
    setForm({ name: "", nummer: "", typ: "Baucluster", farbe: "#f59e0b", gebiet_id: "", project_id: "" });
    setNeuerClusterId(null);
    setVorschau([]);
  }

  function openEdit(c: Cluster) {
    setEditing(c);
    setEditForm({ name: c.name, kuerzel: c.kuerzel ?? "", status: c.status, gebiet_id: c.gebiet_id ?? "", project_id: c.project_id ?? "" });
  }

  async function saveEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editing) return;
    try {
      await adminClusterApi.update(editing.id, {
        ...editForm, gebiet_id: editForm.gebiet_id || null, project_id: editForm.project_id || null,
      });
      toast.success(`Cluster „${editForm.name}" aktualisiert.`);
      setEditing(null);
      load();
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Cluster konnte nicht aktualisiert werden.");
    }
  }

  async function handleDelete(c: Cluster) {
    const ok = await confirmDialog("Cluster endgültig löschen?", `„${c.name}" wird unwiderruflich gelöscht. Zugeordnete Trassen/Objekte verlieren ihre Cluster-Zuordnung, werden aber nicht gelöscht.`, true);
    if (!ok) return;
    try {
      await adminClusterApi.remove(c.id);
      toast.success(`Cluster „${c.name}" gelöscht.`);
      load();
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Löschen fehlgeschlagen.");
    }
  }

  function toggleMergeSelection(id: string) {
    setMergeSelection((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  async function requestMergeVorschau() {
    try {
      const res = await adminClusterApi.mergeVorschau(Array.from(mergeSelection));
      setMergeVorschau(res.data);
      setMergeForm({ name: res.data.vorschlag_name, gebiet_id: "" });
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Vorschau fehlgeschlagen.");
    }
  }

  async function confirmMerge() {
    try {
      await adminClusterApi.merge({
        cluster_ids: Array.from(mergeSelection), name: mergeForm.name,
        gebiet_id: mergeForm.gebiet_id || null,
      });
      toast.success(`${mergeSelection.size} Cluster zu „${mergeForm.name}" zusammengeführt.`);
      setMergeMode(false);
      setMergeSelection(new Set());
      setMergeVorschau(null);
      load();
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Zusammenführen fehlgeschlagen.");
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100">Cluster</h2>
          <p className="text-sm text-slate-500">Räumlich/technisch zusammengehörige Ausbau-, Bau- oder Versorgungsbereiche.</p>
        </div>
        {step === "liste" && !mergeMode && (
          <div className="flex gap-2">
            <button onClick={() => setMergeMode(true)} className="bg-paper-dim dark:bg-slate-700 rounded-lg px-4 py-2 text-sm font-medium">
              Zusammenführen…
            </button>
            <button onClick={() => setStep("zeichnen")} className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">
              + Neuer Cluster
            </button>
          </div>
        )}
        {step === "liste" && mergeMode && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-ink-400">{mergeSelection.size} ausgewählt</span>
            <button
              onClick={requestMergeVorschau}
              disabled={mergeSelection.size < 2}
              className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40"
            >
              Vorschau
            </button>
            <button onClick={() => { setMergeMode(false); setMergeSelection(new Set()); }} className="text-sm text-ink-400 hover:text-slate-700">
              Abbrechen
            </button>
          </div>
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
            <button onClick={() => { toast.success("Cluster ohne Objektzuordnung gespeichert."); resetWizard(); }} className="bg-paper-dim dark:bg-slate-700 rounded-lg px-4 py-2 text-sm">
              Ohne Zuordnung übernehmen
            </button>
          </div>
        </div>
      )}

      {step === "liste" && (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
          {clusters.map((c) => (
            <div key={c.id} className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50">
              {mergeMode && (
                <input type="checkbox" checked={mergeSelection.has(c.id)} onChange={() => toggleMergeSelection(c.id)}
                       className="mr-3 h-4 w-4" />
              )}
              <button
                onClick={() => (mergeMode ? toggleMergeSelection(c.id) : navigate(c.id))}
                className="flex-1 flex items-center gap-3 text-left"
              >
                <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: c.farbe }} />
                <div>
                  <p className="text-sm font-medium text-ink-900 dark:text-slate-100">
                    {c.name} {c.nummer && <span className="text-ink-400 font-normal">({c.nummer})</span>}
                  </p>
                  <p className="text-xs text-slate-400">{c.typ} {c.flaeche_m2 ? `· ${(c.flaeche_m2 / 10000).toFixed(1)} ha` : ""}</p>
                </div>
              </button>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{STATUS_LABEL[c.status] ?? c.status}</span>
                {!mergeMode && (
                  <>
                    <button onClick={() => openEdit(c)} className="text-xs text-brand-600 hover:underline">Bearbeiten</button>
                    <button onClick={() => handleDelete(c)} className="text-xs text-red-600 hover:underline">Löschen</button>
                  </>
                )}
              </div>
            </div>
          ))}
          {clusters.length === 0 && <p className="p-4 text-sm text-slate-400">Noch keine Cluster angelegt.</p>}
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 animate-fade-in" onClick={() => setEditing(null)}>
          <form onSubmit={saveEdit} className="bg-white dark:bg-slate-800 rounded-lg p-5 w-96 shadow-2xl animate-modal-in space-y-3" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-display font-semibold text-lg text-ink-900 dark:text-slate-100">Cluster bearbeiten</h3>
            <input required value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                   className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
            <div className="grid grid-cols-2 gap-2">
              <input placeholder="Kürzel" value={editForm.kuerzel} onChange={(e) => setEditForm({ ...editForm, kuerzel: e.target.value })}
                     className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
              <select value={editForm.status} onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                      className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
                {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-ink-400">Gebiet (verschieben)</label>
              <select value={editForm.gebiet_id} onChange={(e) => setEditForm({ ...editForm, gebiet_id: e.target.value })}
                      className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm mt-0.5">
                <option value="">– kein Gebiet –</option>
                {areas.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-ink-400">Projekt</label>
              <select value={editForm.project_id} onChange={(e) => setEditForm({ ...editForm, project_id: e.target.value })}
                      className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm mt-0.5">
                <option value="">– kein Projekt –</option>
                {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="flex gap-2 pt-1">
              <button type="button" onClick={() => setEditing(null)} className="flex-1 bg-paper-dim dark:bg-slate-700 rounded-md py-2 text-sm">Abbrechen</button>
              <button type="submit" className="flex-1 bg-ink-900 text-white rounded-md py-2 text-sm font-medium">Speichern</button>
            </div>
          </form>
        </div>
      )}

      {mergeVorschau && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 animate-fade-in" onClick={() => setMergeVorschau(null)}>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-5 w-96 shadow-2xl animate-modal-in space-y-3" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-display font-semibold text-lg text-ink-900 dark:text-slate-100">Cluster zusammenführen</h3>
            <dl className="text-sm space-y-1">
              <div className="flex justify-between"><dt className="text-slate-400">Anzahl Cluster</dt><dd>{mergeVorschau.anzahl_cluster}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Kombinierte Fläche</dt><dd>{(mergeVorschau.kombinierte_flaeche_m2 / 10000).toFixed(2)} ha</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Trassen</dt><dd>{mergeVorschau.anzahl_trassen}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Netzelemente</dt><dd>{mergeVorschau.anzahl_netzelemente}</dd></div>
            </dl>
            {mergeVorschau.unterschiedliche_gebiete && (
              <p className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-900/30 rounded-md px-2 py-1.5">
                Ausgewählte Cluster gehören zu unterschiedlichen Gebieten - bitte Ziel-Gebiet für den neuen Cluster wählen.
              </p>
            )}
            <input required placeholder="Name des neuen Clusters" value={mergeForm.name} onChange={(e) => setMergeForm({ ...mergeForm, name: e.target.value })}
                   className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
            <select value={mergeForm.gebiet_id} onChange={(e) => setMergeForm({ ...mergeForm, gebiet_id: e.target.value })}
                    className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              <option value="">– kein Gebiet –</option>
              {areas.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <div className="flex gap-2 pt-1">
              <button type="button" onClick={() => setMergeVorschau(null)} className="flex-1 bg-paper-dim dark:bg-slate-700 rounded-md py-2 text-sm">Abbrechen</button>
              <button type="button" onClick={confirmMerge} className="flex-1 bg-ink-900 text-white rounded-md py-2 text-sm font-medium">Zusammenführen</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

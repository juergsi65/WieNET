import { useState } from "react";
import { editApi } from "../lib/api";
import { toast } from "../store/useToastStore";

interface Props {
  laengeM: number;
  clusters: { id: string; name: string }[];
  onCreated: () => void;
  onCancel: () => void;
}

const ROHR_TYPEN = ["Mikrorohr", "Schutzrohr", "Leerrohr"];

export function TrasseFormModal({
  geometrie, laengeM, clusters, onCreated, onCancel,
}: { geometrie: any } & Props) {
  const [form, setForm] = useState({
    name: "", typ: "Zubringer", status: "geplant", verlegetiefe_cm: "60",
    oberflaeche: "Asphalt", cluster_id: "", anzahl_rohre: "7",
    rohr_typ: "Mikrorohr", rohr_durchmesser: "10",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await editApi.createTrasse({
        name: form.name,
        typ: form.typ,
        status: form.status,
        verlegetiefe_cm: form.verlegetiefe_cm ? Number(form.verlegetiefe_cm) : null,
        oberflaeche: form.oberflaeche,
        geometrie,
        cluster_id: form.cluster_id || null,
        anzahl_rohre: Number(form.anzahl_rohre) || 0,
        rohr_definition: { typ: form.rohr_typ, durchmesser_mm: Number(form.rohr_durchmesser) },
      });
      toast.success(`Trasse "${form.name}" angelegt (Planung).`);
      onCreated();
    } catch (err: any) {
      const msg = err.response?.data?.detail ?? "Trasse konnte nicht angelegt werden.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 animate-fade-in" onClick={onCancel}>
      <div className="bg-white dark:bg-slate-800 rounded-lg p-5 w-[26rem] shadow-2xl max-h-[90vh] overflow-y-auto animate-modal-in" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-display font-semibold text-lg text-ink-900 dark:text-slate-100 mb-1">Neue Trasse</h3>
        <p className="text-xs text-ink-400 mb-4 font-data">{laengeM.toFixed(0)} m gezeichnet</p>

        <form onSubmit={handleSubmit} className="space-y-3">
          {error && <p className="text-sm text-conduit-700 bg-conduit-50 rounded-md px-3 py-2">{error}</p>}

          <input required autoFocus placeholder="Name (z.B. Trasse Musterstraße)" value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />

          <div className="grid grid-cols-2 gap-2">
            <select value={form.typ} onChange={(e) => setForm({ ...form, typ: e.target.value })}
                    className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              {["Haupttrasse", "Zubringer", "Hauszuführung"].map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}
                    className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              {["geplant", "aktiv", "stillgelegt"].map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <input type="number" placeholder="Verlegetiefe (cm)" value={form.verlegetiefe_cm}
                   onChange={(e) => setForm({ ...form, verlegetiefe_cm: e.target.value })}
                   className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
            <select value={form.oberflaeche} onChange={(e) => setForm({ ...form, oberflaeche: e.target.value })}
                    className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              {["Asphalt", "Pflaster", "Wiese", "Schotter"].map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>

          <select value={form.cluster_id} onChange={(e) => setForm({ ...form, cluster_id: e.target.value })}
                  className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
            <option value="">– keinem Cluster zuordnen –</option>
            {clusters.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>

          <div className="border-t border-ink-100 dark:border-slate-700 pt-3">
            <p className="text-xs font-medium uppercase tracking-wide text-ink-400 mb-2">Rohrverband (optional)</p>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="text-xs text-ink-400">Anzahl Rohre</label>
                <input type="number" min="0" max="12" value={form.anzahl_rohre}
                       onChange={(e) => setForm({ ...form, anzahl_rohre: e.target.value })}
                       className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-2 py-1.5 text-sm mt-0.5" />
              </div>
              <div>
                <label className="text-xs text-ink-400">Typ</label>
                <select value={form.rohr_typ} onChange={(e) => setForm({ ...form, rohr_typ: e.target.value })}
                        className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-2 py-1.5 text-sm mt-0.5">
                  {ROHR_TYPEN.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-ink-400">Ø (mm)</label>
                <input type="number" value={form.rohr_durchmesser}
                       onChange={(e) => setForm({ ...form, rohr_durchmesser: e.target.value })}
                       className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-2 py-1.5 text-sm mt-0.5" />
              </div>
            </div>
            <p className="text-xs text-ink-400 mt-1.5">0 = kein Rohrverband, nur die Trasse selbst wird angelegt.</p>
          </div>

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onCancel} className="flex-1 bg-paper-dim dark:bg-slate-700 rounded-md py-2 text-sm">Abbrechen</button>
            <button type="submit" disabled={loading} className="flex-1 bg-ink-900 text-white rounded-md py-2 text-sm font-medium disabled:opacity-50">
              {loading ? "Speichert…" : "Trasse anlegen"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

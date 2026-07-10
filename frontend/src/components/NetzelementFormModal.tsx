import { useState } from "react";
import { editApi } from "../lib/api";
import { toast } from "../store/useToastStore";

interface Props {
  typ: string;
  typLabel: string;
  clusters: { id: string; name: string }[];
  onCreated: (feature: any) => void;
  onCancel: () => void;
}

const PORTS_TYPEN = ["verteiler", "fcp"]; // Typen, bei denen eine Portanzahl sinnvoll ist

export default function NetzelementFormModal({
  typ, typLabel, geometrie, clusters, onCreated, onCancel,
}: Props & { geometrie: any }) {
  const [form, setForm] = useState({
    name: "", status: "geplant", cluster_id: "", ports_gesamt: "", notizen: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await editApi.createNetzelement({
        name: form.name, typ, status: form.status, geometrie,
        cluster_id: form.cluster_id || null,
        ports_gesamt: PORTS_TYPEN.includes(typ) && form.ports_gesamt ? Number(form.ports_gesamt) : null,
        notizen: form.notizen || null,
      });
      toast.success(`${typLabel} "${form.name}" angelegt (Planung).`);
      onCreated({
        type: "Feature",
        geometry: geometrie,
        properties: {
          id: res.data.id, name: form.name, typ, status: form.status,
          ports_gesamt: PORTS_TYPEN.includes(typ) && form.ports_gesamt ? Number(form.ports_gesamt) : null,
          ports_belegt: 0, belegung_pct: null, objekt_typ: "netzelement",
          ist_planung: form.status === "geplant", erstellt_von: null, planungskennzeichen: null,
        },
      });
    } catch (err: any) {
      const msg = err.response?.data?.detail ?? `${typLabel} konnte nicht angelegt werden.`;
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 animate-fade-in" onClick={onCancel}>
      <div className="bg-white dark:bg-slate-800 rounded-lg p-5 w-96 shadow-2xl animate-modal-in" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-display font-semibold text-lg text-ink-900 dark:text-slate-100 mb-4">Neu: {typLabel}</h3>

        <form onSubmit={handleSubmit} className="space-y-3">
          {error && <p className="text-sm text-conduit-700 bg-conduit-50 rounded-md px-3 py-2">{error}</p>}

          <input required autoFocus placeholder={`Name (z.B. ${typLabel}-001)`} value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />

          <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
            {["geplant", "aktiv", "stillgelegt"].map((s) => <option key={s} value={s}>{s}</option>)}
          </select>

          <select value={form.cluster_id} onChange={(e) => setForm({ ...form, cluster_id: e.target.value })}
                  className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
            <option value="">– keinem Cluster zuordnen –</option>
            {clusters.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>

          {PORTS_TYPEN.includes(typ) && (
            <input type="number" placeholder="Anzahl Ports" value={form.ports_gesamt}
                   onChange={(e) => setForm({ ...form, ports_gesamt: e.target.value })}
                   className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
          )}

          <textarea placeholder="Notizen (optional)" value={form.notizen} rows={2}
                    onChange={(e) => setForm({ ...form, notizen: e.target.value })}
                    className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onCancel} className="flex-1 bg-paper-dim dark:bg-slate-700 rounded-md py-2 text-sm">Abbrechen</button>
            <button type="submit" disabled={loading} className="flex-1 bg-ink-900 text-white rounded-md py-2 text-sm font-medium disabled:opacity-50">
              {loading ? "Speichert…" : "Anlegen"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

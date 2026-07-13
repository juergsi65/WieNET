import { useEffect, useState } from "react";
import { numberingApi } from "../../lib/api";
import { toast } from "../../store/useToastStore";
import { confirmDialog } from "../../store/useConfirmStore";

const ENTITY_TYPES = [
  { value: "gebiet", label: "Gebiet" },
  { value: "cluster", label: "Cluster" },
  { value: "projekt", label: "Projekt" },
  { value: "bauabschnitt", label: "Bauabschnitt" },
  { value: "trasse", label: "Trasse" },
];

const SCOPES: Record<string, { value: string; label: string }[]> = {
  gebiet: [{ value: "global", label: "Global (ein Zähler für alle Gebiete)" }],
  cluster: [
    { value: "global", label: "Global (ein Zähler für alle Cluster)" },
    { value: "gebiet", label: "Pro Gebiet (Zähler startet je Gebiet neu)" },
    { value: "projekt", label: "Pro Projekt" },
  ],
  projekt: [{ value: "global", label: "Global" }],
  bauabschnitt: [
    { value: "global", label: "Global" },
    { value: "projekt", label: "Pro Projekt" },
    { value: "cluster", label: "Pro Cluster" },
  ],
  trasse: [
    { value: "global", label: "Global" },
    { value: "cluster", label: "Pro Cluster" },
    { value: "gebiet", label: "Pro Gebiet" },
  ],
};

export default function NumberingManagement() {
  const [schemata, setSchemata] = useState<any[]>([]);
  const [form, setForm] = useState({ entity_type: "gebiet", name: "", pattern: "G-{sequence:03d}", scope: "global", start_value: "1" });
  const [preview, setPreview] = useState<string | null>(null);
  const [previewFehler, setPreviewFehler] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    numberingApi.list().then((r) => setSchemata(r.data));
  }
  useEffect(load, []);

  // Live-Vorschau des Musters während der Eingabe (rein clientseitige Formatierung,
  // ohne den serverseitigen Zähler zu berühren - nur zur Kontrolle der Syntax)
  useEffect(() => {
    setPreviewFehler(null);
    try {
      if (!form.pattern.includes("{sequence")) {
        setPreview(null);
        return;
      }
      const beispiel = form.pattern
        .replace(/\{sequence:0(\d)d\}/, (_, n) => String(Number(form.start_value)).padStart(Number(n), "0"))
        .replace(/\{sequence\}/, String(form.start_value))
        .replace(/\{gebiet_code\}/, "WAL-N")
        .replace(/\{cluster_code\}/, "C01")
        .replace(/\{projekt_code\}/, "PRJ01")
        .replace(/\{jahr\}/, String(new Date().getFullYear()));
      setPreview(beispiel);
    } catch {
      setPreview(null);
    }
  }, [form.pattern, form.start_value]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await numberingApi.create({
        entity_type: form.entity_type, name: form.name, pattern: form.pattern,
        scope: form.scope, start_value: Number(form.start_value) || 1,
      });
      toast.success(`Nummernschema „${form.name}" angelegt.`);
      setForm({ ...form, name: "" });
      load();
    } catch (e: any) {
      const msg = e.response?.data?.detail ?? "Schema konnte nicht angelegt werden.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
      toast.error(typeof msg === "string" ? msg : "Ungültiges Muster.");
    }
  }

  async function activate(id: string, name: string) {
    const ok = await confirmDialog("Schema aktivieren?", `„${name}" wird zum aktiven Nummernschema für diesen Objekttyp - ein evtl. vorher aktives Schema wird deaktiviert (bleibt aber historisch erhalten).`);
    if (!ok) return;
    try {
      await numberingApi.activate(id);
      toast.success("Schema aktiviert.");
      load();
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Aktivierung fehlgeschlagen.");
    }
  }

  async function remove(id: string, name: string) {
    const ok = await confirmDialog("Schema löschen?", `„${name}" wird endgültig gelöscht.`, true);
    if (!ok) return;
    try {
      await numberingApi.remove(id);
      toast.success("Schema gelöscht.");
      load();
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Löschen fehlgeschlagen.");
    }
  }

  const gruppiert = ENTITY_TYPES.map((et) => ({
    ...et,
    schemata: schemata.filter((s) => s.entity_type === et.value),
  }));

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100">Nummernkreise</h2>
        <p className="text-sm text-slate-500">
          Konfigurierbare, transaktionssichere Nummernvergabe. Je Objekttyp ist höchstens ein Schema aktiv;
          ohne aktives Schema bleibt die Nummer frei editierbar wie bisher.
        </p>
      </div>

      <form onSubmit={submit} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 space-y-3 mb-6">
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Objekttyp</label>
            <select value={form.entity_type} onChange={(e) => setForm({ ...form, entity_type: e.target.value, scope: "global" })}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              {ENTITY_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Name</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="z.B. Standard"
                   className="w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Geltungsbereich</label>
            <select value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              {(SCOPES[form.entity_type] ?? SCOPES.gebiet).map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Startwert</label>
            <input type="number" min="1" value={form.start_value} onChange={(e) => setForm({ ...form, start_value: e.target.value })}
                   className="w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
          </div>
          <div className="col-span-2">
            <label className="text-xs text-slate-400 block mb-1">
              Muster - Platzhalter: {"{sequence:03d}"} (Pflicht), {"{gebiet_code}"}, {"{cluster_code}"}, {"{projekt_code}"}, {"{jahr}"}
            </label>
            <input required value={form.pattern} onChange={(e) => setForm({ ...form, pattern: e.target.value })}
                   className="w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm font-mono" />
            {preview && <p className="text-xs text-signal-600 mt-1">Beispiel: {preview}</p>}
            {previewFehler && <p className="text-xs text-red-600 mt-1">{previewFehler}</p>}
          </div>
        </div>
        <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">Schema anlegen</button>
      </form>

      <div className="space-y-5">
        {gruppiert.map((g) => (
          <div key={g.value}>
            <p className="text-xs font-semibold uppercase tracking-wide text-ink-400 mb-1.5">{g.label}</p>
            <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
              {g.schemata.map((s) => (
                <div key={s.id} className="flex items-center justify-between px-4 py-2.5">
                  <div>
                    <p className="text-sm text-ink-900 dark:text-slate-100">
                      {s.name} <span className="font-mono text-xs text-slate-400 ml-1">{s.pattern}</span>
                    </p>
                    <p className="text-xs text-slate-400">Geltungsbereich: {s.scope} · Start: {s.start_value}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {s.aktiv ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-signal-100 text-signal-700 font-medium">aktiv</span>
                    ) : (
                      <>
                        <button onClick={() => activate(s.id, s.name)} className="text-xs text-brand-600 hover:underline">Aktivieren</button>
                        <button onClick={() => remove(s.id, s.name)} className="text-xs text-red-600 hover:underline">Löschen</button>
                      </>
                    )}
                  </div>
                </div>
              ))}
              {g.schemata.length === 0 && <p className="px-4 py-2.5 text-sm text-slate-400">Kein Schema konfiguriert.</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

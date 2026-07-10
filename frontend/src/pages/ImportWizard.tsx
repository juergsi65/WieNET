import { useState } from "react";
import { api } from "../lib/api";

const OBJEKT_TYPEN = [
  { value: "schacht", label: "Schacht" },
  { value: "muffe", label: "Muffe" },
  { value: "verteiler", label: "Verteiler" },
  { value: "fcp", label: "FCP" },
  { value: "hausanschluss", label: "Hausanschluss" },
  { value: "gebaeude", label: "Gebäude" },
];

type Step = "datei" | "vorschau" | "zuordnung" | "ergebnis";

export default function ImportWizard() {
  const [step, setStep] = useState<Step>("datei");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [objektTyp, setObjektTyp] = useState("schacht");
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileSelected(f: File) {
    setFile(f);
    setError(null);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", f);
      const res = await api.post("/import/preview", formData, { headers: { "Content-Type": "multipart/form-data" } });
      setPreview(res.data);
      setStep("vorschau");
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Datei konnte nicht gelesen werden.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCommit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("objekt_typ", objektTyp);
      formData.append("spalten_mapping", JSON.stringify(mapping));
      const res = await api.post("/import/commit", formData, { headers: { "Content-Type": "multipart/form-data" } });
      setResult(res.data);
      setStep("ergebnis");
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Import fehlgeschlagen.");
    } finally {
      setLoading(false);
    }
  }

  const spalten: string[] = preview?.spalten ?? preview?.erkannte_eigenschaften ?? [];

  return (
    <div className="p-6 max-w-3xl mx-auto overflow-y-auto h-full">
      <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100 mb-1">Datenimport</h2>
      <p className="text-sm text-ink-400 mb-6">CSV, Excel oder GeoJSON importieren – mit Vorschau und Validierung.</p>

      <div className="flex gap-2 mb-6 text-xs">
        {(["datei", "vorschau", "zuordnung", "ergebnis"] as Step[]).map((s, i) => (
          <div key={s} className={`px-3 py-1 rounded-full ${step === s ? "bg-brand-600 text-white" : "bg-slate-100 dark:bg-slate-700 text-slate-500"}`}>
            {i + 1}. {s}
          </div>
        ))}
      </div>

      {error && <div className="mb-4 text-sm text-conduit-600 bg-red-50 rounded-lg p-3">{error}</div>}

      {step === "datei" && (
        <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-10 text-center">
          <p className="text-sm text-ink-400 mb-3">CSV, Excel (.xlsx) oder GeoJSON auswählen</p>
          <input
            type="file" accept=".csv,.xlsx,.xls,.geojson,.json"
            onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
            className="mx-auto text-sm"
          />
          {loading && <p className="text-sm text-ink-400 mt-3">Datei wird analysiert…</p>}
        </div>
      )}

      {step === "vorschau" && preview && (
        <div>
          <p className="text-sm text-slate-600 dark:text-slate-300 mb-2">
            {preview.anzahl_zeilen} Datensätze erkannt. Erste Zeilen zur Kontrolle:
          </p>
          <div className="overflow-x-auto border border-ink-100 dark:border-slate-700 rounded-lg mb-4">
            <table className="text-xs w-full">
              <thead className="bg-slate-50 dark:bg-slate-700">
                <tr>{spalten.map((c) => <th key={c} className="text-left px-2 py-1.5 font-medium">{c}</th>)}</tr>
              </thead>
              <tbody>
                {preview.vorschau.slice(0, 8).map((row: any, i: number) => (
                  <tr key={i} className="border-t border-slate-100 dark:border-slate-700">
                    {spalten.map((c) => <td key={c} className="px-2 py-1.5">{String(row[c] ?? row.properties?.[c] ?? "")}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button onClick={() => setStep("zuordnung")} className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">
            Weiter zur Spaltenzuordnung
          </button>
        </div>
      )}

      {step === "zuordnung" && (
        <div className="space-y-4">
          <div>
            <label className="text-sm text-slate-600 dark:text-slate-300">Zielobjekttyp</label>
            <select value={objektTyp} onChange={(e) => setObjektTyp(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
              {OBJEKT_TYPEN.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          {["name", "lat", "lon", "adresse"].map((field) => (
            <div key={field}>
              <label className="text-sm text-slate-600 dark:text-slate-300 capitalize">
                Spalte für "{field}" {field !== "adresse" && <span className="text-red-500">*</span>}
              </label>
              <select
                value={mapping[field] ?? ""}
                onChange={(e) => setMapping((m) => ({ ...m, [field]: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm"
              >
                <option value="">– nicht zuordnen –</option>
                {spalten.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          ))}
          <button
            onClick={handleCommit}
            disabled={loading || !mapping.name || !mapping.lat || !mapping.lon}
            className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Importiere…" : "Import bestätigen"}
          </button>
        </div>
      )}

      {step === "ergebnis" && result && (
        <div>
          <div className={`rounded-lg p-4 mb-4 ${result.erfolgreich ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"}`}>
            {result.importiert} Datensätze erfolgreich importiert.
            {result.fehler.length > 0 && ` ${result.fehler.length} Zeilen mit Fehlern übersprungen.`}
          </div>
          {result.fehler.length > 0 && (
            <ul className="text-xs text-ink-400 space-y-1 max-h-48 overflow-y-auto">
              {result.fehler.map((f: any, i: number) => (
                <li key={i}>Zeile {f.zeile}: {f.fehler}</li>
              ))}
            </ul>
          )}
          <button
            onClick={() => { setStep("datei"); setFile(null); setPreview(null); setResult(null); setMapping({}); }}
            className="mt-4 bg-slate-100 dark:bg-slate-700 rounded-lg px-4 py-2 text-sm"
          >
            Weiteren Import starten
          </button>
        </div>
      )}
    </div>
  );
}

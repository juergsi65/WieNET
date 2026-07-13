import { useEffect, useState } from "react";
import { materialApi } from "../../lib/api";
import { toast } from "../../store/useToastStore";
import { confirmDialog } from "../../store/useConfirmStore";

type Tab = "hersteller" | "kategorien" | "farben" | "produktfamilien" | "produkte" | "rohrverbaende" | "kabel";

const TABS: { key: Tab; label: string }[] = [
  { key: "hersteller", label: "Hersteller" },
  { key: "kategorien", label: "Produktkategorien" },
  { key: "farben", label: "Farben" },
  { key: "produktfamilien", label: "Produktfamilien" },
  { key: "produkte", label: "Produkte" },
  { key: "rohrverbaende", label: "Rohrverbandvorlagen" },
  { key: "kabel", label: "Kabelvorlagen" },
];

async function handleDelete(objName: string, remove: () => Promise<any>, reload: () => void) {
  const ok = await confirmDialog("Endgültig löschen?", `„${objName}" wird unwiderruflich gelöscht.`, true);
  if (!ok) return;
  try {
    await remove();
    toast.success(`„${objName}" gelöscht.`);
    reload();
  } catch (e: any) {
    toast.error(e.response?.data?.detail ?? "Löschen fehlgeschlagen.");
  }
}

export default function MaterialCatalog() {
  const [tab, setTab] = useState<Tab>("hersteller");

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100">Materialkatalog</h2>
        <p className="text-sm text-slate-500">
          Hersteller, Produkte, Farben und Rohrverband-/Kabelvorlagen für die Materialauswahl im Redlining.
          Offizielle Herstellerangaben sind mit Quelle gekennzeichnet - fehlende Angaben bitte mit verifizierten
          Datenblättern ergänzen, nicht schätzen.
        </p>
      </div>

      <div className="flex gap-1 mb-4 overflow-x-auto border-b border-ink-100 dark:border-slate-700">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`whitespace-nowrap px-3 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              tab === t.key
                ? "border-conduit-500 text-conduit-700 dark:text-conduit-300"
                : "border-transparent text-ink-500 dark:text-slate-400 hover:text-ink-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "hersteller" && <HerstellerTab />}
      {tab === "kategorien" && <KategorienTab />}
      {tab === "farben" && <FarbenTab />}
      {tab === "produktfamilien" && <ProduktfamilienTab />}
      {tab === "produkte" && <ProdukteTab />}
      {tab === "rohrverbaende" && <RohrverbandTab />}
      {tab === "kabel" && <KabelTab />}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="p-4 text-sm text-slate-400">{text}</p>;
}

function SourceBadge({ url, offiziell }: { url?: string | null; offiziell?: boolean }) {
  if (offiziell === false) {
    return <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-500">benutzerdefiniert</span>;
  }
  return url ? (
    <a href={url} target="_blank" rel="noreferrer" className="text-xs text-brand-600 hover:underline">Quelle ↗</a>
  ) : (
    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">zu ergänzen</span>
  );
}

// --- Hersteller ---

function HerstellerTab() {
  const [items, setItems] = useState<any[]>([]);
  const [form, setForm] = useState({ name: "", website: "" });
  const [error, setError] = useState<string | null>(null);

  function load() {
    materialApi.hersteller.list().then((r) => setItems(r.data));
  }
  useEffect(load, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await materialApi.hersteller.create({ name: form.name, website: form.website || null, quelle_url: form.website || null });
      setForm({ name: "", website: "" });
      load();
      toast.success(`Hersteller „${form.name}" angelegt.`);
    } catch (e: any) {
      const msg = e.response?.data?.detail ?? "Hersteller konnte nicht angelegt werden.";
      setError(msg);
      toast.error(msg);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 flex flex-wrap gap-3 items-end">
        {error && <p className="text-sm text-red-600 w-full">{error}</p>}
        <div>
          <label className="text-xs text-slate-400 block mb-1">Name</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-64" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Website / Quelle</label>
          <input value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} placeholder="https://..."
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-72" />
        </div>
        <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">Hersteller anlegen</button>
      </form>

      <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {items.map((h) => (
          <div key={h.id} className="flex items-center justify-between px-4 py-3">
            <div>
              <p className="text-sm font-medium text-ink-900 dark:text-slate-100">{h.name}</p>
              <SourceBadge url={h.website} />
            </div>
            <button onClick={() => handleDelete(h.name, () => materialApi.hersteller.remove(h.id), load)}
                    className="text-xs text-red-600 hover:underline">Löschen</button>
          </div>
        ))}
        {items.length === 0 && <EmptyState text="Noch keine Hersteller angelegt." />}
      </div>
    </div>
  );
}

// --- Produktkategorien ---

function KategorienTab() {
  const [items, setItems] = useState<any[]>([]);
  const [name, setName] = useState("");

  function load() {
    materialApi.kategorien.list().then((r) => setItems(r.data));
  }
  useEffect(load, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await materialApi.kategorien.create({ name });
      setName("");
      load();
      toast.success(`Kategorie „${name}" angelegt.`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Kategorie konnte nicht angelegt werden.");
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 flex gap-3 items-end">
        <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Kategoriename"
               className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-64" />
        <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">Kategorie anlegen</button>
      </form>
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {items.map((k) => (
          <div key={k.id} className="flex items-center justify-between px-4 py-3">
            <p className="text-sm text-ink-900 dark:text-slate-100">{k.name}</p>
            <button onClick={() => handleDelete(k.name, () => materialApi.kategorien.remove(k.id), load)}
                    className="text-xs text-red-600 hover:underline">Löschen</button>
          </div>
        ))}
        {items.length === 0 && <EmptyState text="Noch keine Kategorien angelegt." />}
      </div>
    </div>
  );
}

// --- Farben ---

function FarbenTab() {
  const [items, setItems] = useState<any[]>([]);
  const [standard, setStandard] = useState<string>("");
  const [form, setForm] = useState({ name: "", kurzcode: "", hex_wert: "#DC2626", farbstandard: "benutzerdefiniert" });

  function load() {
    materialApi.farben.list(standard || undefined).then((r) => setItems(r.data));
  }
  useEffect(load, [standard]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await materialApi.farben.create({ ...form, streifenanzahl: 0 });
      load();
      toast.success(`Farbe „${form.name}" angelegt.`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Farbe konnte nicht angelegt werden.");
    }
  }

  const standards = Array.from(new Set(items.map((f) => f.farbstandard)));

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        <label className="text-xs text-slate-400">Farbstandard filtern:</label>
        <select value={standard} onChange={(e) => setStandard(e.target.value)}
                className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-2 py-1 text-sm">
          <option value="">Alle</option>
          <option value="DIN EN 60794-1-1">DIN EN 60794-1-1</option>
          <option value="TIA-598-C">TIA-598-C</option>
          <option value="benutzerdefiniert">benutzerdefiniert</option>
        </select>
      </div>

      <form onSubmit={submit} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-slate-400 block mb-1">Name</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-40" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Kurzcode</label>
          <input value={form.kurzcode} onChange={(e) => setForm({ ...form, kurzcode: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-24" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Hex (nur UI)</label>
          <input type="color" value={form.hex_wert} onChange={(e) => setForm({ ...form, hex_wert: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 h-10 w-16" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Farbstandard</label>
          <input required value={form.farbstandard} onChange={(e) => setForm({ ...form, farbstandard: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-48" />
        </div>
        <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">Farbe anlegen</button>
      </form>

      <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {items.map((f) => (
          <div key={f.id} className="flex items-center justify-between px-4 py-2.5">
            <div className="flex items-center gap-3">
              <span className="w-4 h-4 rounded-full border border-black/10" style={{ backgroundColor: f.hex_wert ?? "#ccc" }} />
              <p className="text-sm text-ink-900 dark:text-slate-100">
                {f.name} {f.kurzcode && <span className="text-slate-400">({f.kurzcode})</span>}
                {f.streifenanzahl > 0 && <span className="text-xs text-slate-400 ml-1">+ Streifen</span>}
              </p>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-500">{f.farbstandard}</span>
            </div>
            <button onClick={() => handleDelete(f.name, () => materialApi.farben.remove(f.id), load)}
                    className="text-xs text-red-600 hover:underline">Löschen</button>
          </div>
        ))}
        {items.length === 0 && <EmptyState text="Keine Farben gefunden." />}
      </div>
    </div>
  );
}

// --- Produktfamilien ---

function ProduktfamilienTab() {
  const [items, setItems] = useState<any[]>([]);
  const [hersteller, setHersteller] = useState<any[]>([]);
  const [kategorien, setKategorien] = useState<any[]>([]);
  const [form, setForm] = useState({ hersteller_id: "", kategorie_id: "", name: "", quelle_url: "" });

  function load() {
    materialApi.produktfamilien.list().then((r) => setItems(r.data));
    materialApi.hersteller.list().then((r) => setHersteller(r.data));
    materialApi.kategorien.list().then((r) => setKategorien(r.data));
  }
  useEffect(load, []);

  const herstellerName = (id: string) => hersteller.find((h) => h.id === id)?.name ?? "?";
  const kategorieName = (id: string) => kategorien.find((k) => k.id === id)?.name ?? "?";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await materialApi.produktfamilien.create({ ...form, quelle_url: form.quelle_url || null });
      setForm({ ...form, name: "", quelle_url: "" });
      load();
      toast.success(`Produktfamilie „${form.name}" angelegt.`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Produktfamilie konnte nicht angelegt werden.");
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-slate-400 block mb-1">Hersteller</label>
          <select required value={form.hersteller_id} onChange={(e) => setForm({ ...form, hersteller_id: e.target.value })}
                  className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-56">
            <option value="">wählen…</option>
            {hersteller.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Kategorie</label>
          <select required value={form.kategorie_id} onChange={(e) => setForm({ ...form, kategorie_id: e.target.value })}
                  className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-48">
            <option value="">wählen…</option>
            {kategorien.map((k) => <option key={k.id} value={k.id}>{k.name}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Name der Produktfamilie</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-56" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Quelle (Datenblatt-URL)</label>
          <input value={form.quelle_url} onChange={(e) => setForm({ ...form, quelle_url: e.target.value })} placeholder="https://..."
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-72" />
        </div>
        <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">Produktfamilie anlegen</button>
      </form>

      <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {items.map((pf) => (
          <div key={pf.id} className="flex items-center justify-between px-4 py-3">
            <div>
              <p className="text-sm font-medium text-ink-900 dark:text-slate-100">{pf.name}</p>
              <p className="text-xs text-slate-400">{herstellerName(pf.hersteller_id)} · {kategorieName(pf.kategorie_id)}</p>
              <SourceBadge url={pf.quelle_url} />
            </div>
            <button onClick={() => handleDelete(pf.name, () => materialApi.produktfamilien.remove(pf.id), load)}
                    className="text-xs text-red-600 hover:underline">Löschen</button>
          </div>
        ))}
        {items.length === 0 && <EmptyState text="Noch keine Produktfamilien angelegt." />}
      </div>
    </div>
  );
}

// --- Produkte ---

const PRODUKTTYPEN = ["rohrverband", "einzelrohr", "microduct", "schutzrohr", "kabel", "schacht", "muffe", "verteiler", "sonstiges"];

function ProdukteTab() {
  const [items, setItems] = useState<any[]>([]);
  const [familien, setFamilien] = useState<any[]>([]);
  const [form, setForm] = useState({ produktfamilie_id: "", name: "", hersteller_artikelnummer: "", produkttyp: "rohrverband" });

  function load() {
    materialApi.produkte.list().then((r) => setItems(r.data));
    materialApi.produktfamilien.list().then((r) => setFamilien(r.data));
  }
  useEffect(load, []);

  const familieName = (id: string) => familien.find((f) => f.id === id)?.name ?? "?";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await materialApi.produkte.create({ ...form, hersteller_artikelnummer: form.hersteller_artikelnummer || null, benutzerdefiniert: true });
      setForm({ ...form, name: "", hersteller_artikelnummer: "" });
      load();
      toast.success(`Produkt „${form.name}" angelegt.`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Produkt konnte nicht angelegt werden.");
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-slate-400 block mb-1">Produktfamilie</label>
          <select required value={form.produktfamilie_id} onChange={(e) => setForm({ ...form, produktfamilie_id: e.target.value })}
                  className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-56">
            <option value="">wählen…</option>
            {familien.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Produktname / Variante</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-56" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Artikelnummer</label>
          <input value={form.hersteller_artikelnummer} onChange={(e) => setForm({ ...form, hersteller_artikelnummer: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-40" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Typ</label>
          <select value={form.produkttyp} onChange={(e) => setForm({ ...form, produkttyp: e.target.value })}
                  className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
            {PRODUKTTYPEN.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">Produkt anlegen</button>
      </form>

      <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {items.map((p) => (
          <div key={p.id} className="flex items-center justify-between px-4 py-3">
            <div>
              <p className="text-sm font-medium text-ink-900 dark:text-slate-100">
                {p.name} {p.hersteller_artikelnummer && <span className="text-slate-400 font-normal">· Art.-Nr. {p.hersteller_artikelnummer}</span>}
              </p>
              <p className="text-xs text-slate-400">{familieName(p.produktfamilie_id)} · {p.produkttyp}</p>
              <SourceBadge url={p.quelle_url} offiziell={!p.benutzerdefiniert} />
            </div>
            <button onClick={() => handleDelete(p.name, () => materialApi.produkte.remove(p.id), load)}
                    className="text-xs text-red-600 hover:underline">Löschen</button>
          </div>
        ))}
        {items.length === 0 && <EmptyState text="Noch keine Produkte angelegt." />}
      </div>
    </div>
  );
}

// --- Rohrverbandvorlagen ---

function RohrverbandTab() {
  const [items, setItems] = useState<any[]>([]);
  const [farben, setFarben] = useState<any[]>([]);

  function load() {
    materialApi.rohrverbandVorlagen.list().then((r) => setItems(r.data));
    materialApi.farben.list().then((r) => setFarben(r.data));
  }
  useEffect(load, []);

  const farbeById = (id: string) => farben.find((f) => f.id === id);

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-400">
        Neue Rohrverbandvorlagen mit individuellem Rohr-für-Rohr-Aufbau werden über die API angelegt
        (Formular folgt in Phase 2 zusammen mit der Redlining-Integration). Vorhandene Vorlagen:
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        {items.map((v) => (
          <div key={v.id} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-sm font-medium text-ink-900 dark:text-slate-100">{v.name}</p>
                <p className="text-xs text-slate-400">{v.rohranzahl} Rohre · {v.layout_typ}</p>
              </div>
              <button onClick={() => handleDelete(v.name, () => materialApi.rohrverbandVorlagen.remove(v.id), load)}
                      className="text-xs text-red-600 hover:underline">Löschen</button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {v.positionen.map((p: any) => {
                const f = farbeById(p.rohrfarbe_id);
                return (
                  <span key={p.id} title={`Position ${p.position}: ${f?.name ?? "?"}`}
                        className="w-6 h-6 rounded-full border border-black/10 flex items-center justify-center text-[9px] font-semibold text-white"
                        style={{ backgroundColor: f?.hex_wert ?? "#999" }}>
                    {p.position}
                  </span>
                );
              })}
            </div>
          </div>
        ))}
        {items.length === 0 && <EmptyState text="Noch keine Rohrverbandvorlagen angelegt." />}
      </div>
    </div>
  );
}

// --- Kabelvorlagen ---

function KabelTab() {
  const [items, setItems] = useState<any[]>([]);
  const [farben, setFarben] = useState<any[]>([]);
  const [form, setForm] = useState({ name: "", mantelfarbe_id: "", faseranzahl: "24", kabeltyp: "glasfaser", faserstandard: "TIA-598-C" });

  function load() {
    materialApi.kabelVorlagen.list().then((r) => setItems(r.data));
    materialApi.farben.list().then((r) => setFarben(r.data));
  }
  useEffect(load, []);

  const farbeName = (id: string | null) => farben.find((f) => f.id === id)?.name ?? "–";

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await materialApi.kabelVorlagen.create({
        ...form, mantelfarbe_id: form.mantelfarbe_id || null,
        faseranzahl: form.faseranzahl ? Number(form.faseranzahl) : null,
      });
      setForm({ ...form, name: "" });
      load();
      toast.success(`Kabelvorlage „${form.name}" angelegt.`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Kabelvorlage konnte nicht angelegt werden.");
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-slate-400 block mb-1">Name</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-48" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Mantelfarbe</label>
          <select value={form.mantelfarbe_id} onChange={(e) => setForm({ ...form, mantelfarbe_id: e.target.value })}
                  className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-40">
            <option value="">keine</option>
            {farben.map((f) => <option key={f.id} value={f.id}>{f.name} ({f.farbstandard})</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Faseranzahl</label>
          <input type="number" value={form.faseranzahl} onChange={(e) => setForm({ ...form, faseranzahl: e.target.value })}
                 className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm w-24" />
        </div>
        <div>
          <label className="text-xs text-slate-400 block mb-1">Typ</label>
          <select value={form.kabeltyp} onChange={(e) => setForm({ ...form, kabeltyp: e.target.value })}
                  className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
            <option value="glasfaser">Glasfaser</option>
            <option value="kupfer">Kupfer</option>
          </select>
        </div>
        <button type="submit" className="bg-brand-600 text-white rounded-lg px-4 py-2 text-sm font-medium">Kabelvorlage anlegen</button>
      </form>

      <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {items.map((k) => (
          <div key={k.id} className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              {k.mantelfarbe_id && <span className="w-4 h-4 rounded-full border border-black/10" style={{ backgroundColor: farben.find((f) => f.id === k.mantelfarbe_id)?.hex_wert }} />}
              <div>
                <p className="text-sm font-medium text-ink-900 dark:text-slate-100">{k.name}</p>
                <p className="text-xs text-slate-400">{k.kabeltyp} · {farbeName(k.mantelfarbe_id)} · {k.faseranzahl ?? "–"} Fasern</p>
              </div>
            </div>
            <button onClick={() => handleDelete(k.name, () => materialApi.kabelVorlagen.remove(k.id), load)}
                    className="text-xs text-red-600 hover:underline">Löschen</button>
          </div>
        ))}
        {items.length === 0 && <EmptyState text="Noch keine Kabelvorlagen angelegt." />}
      </div>
    </div>
  );
}

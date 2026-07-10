import { useEffect, useState } from "react";
import { rohrbelegungApi, editApi } from "../lib/api";
import { toast } from "../store/useToastStore";

interface RohrBelegung {
  rohr: { id: string; nummer: number; farbe: string; durchmesser_mm: number | null; typ: string | null; status: string };
  kabel: { id: string; bezeichnung: string; typ: string; fasernanzahl: number | null; belegte_fasern: number; status: string } | null;
  segment_start_m: number | null;
  segment_ende_m: number | null;
}

interface Rohrverband {
  id: string;
  bezeichnung: string;
  trasse_id: string;
  rohre: RohrBelegung[];
}

const STATUS_LABEL: Record<string, string> = {
  frei: "Frei", belegt: "Belegt", reserviert: "Reserviert", blockiert: "Blockiert", beschaedigt: "Beschädigt",
};

function ringLayout(count: number, radius = 70) {
  const positions: { x: number; y: number }[] = [];
  if (count === 1) return [{ x: 0, y: 0 }];
  for (let i = 0; i < count; i++) {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2;
    positions.push({ x: radius * Math.cos(angle), y: radius * Math.sin(angle) });
  }
  return positions;
}

export default function RohrQuerschnitt({ trasseId, canEdit = false }: { trasseId: string; canEdit?: boolean }) {
  const [verbaende, setVerbaende] = useState<Rohrverband[]>([]);
  const [hovered, setHovered] = useState<RohrBelegung | null>(null);
  const [selected, setSelected] = useState<RohrBelegung | null>(null);
  const [loading, setLoading] = useState(true);

  function reload() {
    setLoading(true);
    rohrbelegungApi
      .fuerTrasse(trasseId)
      .then((res) => setVerbaende(res.data))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trasseId]);

  if (loading) return <div className="text-sm text-ink-400 p-4">Rohrbelegung wird geladen…</div>;
  if (verbaende.length === 0) return <div className="text-sm text-ink-400 p-4">Kein Rohrverband auf dieser Trasse hinterlegt.</div>;

  return (
    <div className="space-y-6">
      {verbaende.map((rv) => {
        const positions = ringLayout(rv.rohre.length);
        return (
          <div key={rv.id} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4">
            <h4 className="text-sm font-semibold text-ink-600 dark:text-slate-200 mb-2">{rv.bezeichnung}</h4>
            <div className="flex gap-4 items-start flex-wrap">
              <svg viewBox="-100 -100 200 200" className="w-48 h-48 shrink-0">
                <circle cx={0} cy={0} r={90} fill="none" stroke="#cbd5e1" strokeWidth={1.5} strokeDasharray="3,3" />
                {rv.rohre.map((rb, idx) => {
                  const pos = positions[idx];
                  const belegt = !!rb.kabel;
                  return (
                    <g
                      key={rb.rohr.id}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onMouseEnter={() => setHovered(rb)}
                      onMouseLeave={() => setHovered(null)}
                      onClick={() => setSelected(rb)}
                      style={{ cursor: "pointer" }}
                    >
                      <circle
                        r={18}
                        fill={belegt ? rb.rohr.farbe : "#ffffff"}
                        stroke={rb.rohr.status === "blockiert" ? "#dc2626" : rb.rohr.status === "beschaedigt" ? "#f59e0b" : "#475569"}
                        strokeWidth={rb.rohr.status === "blockiert" || rb.rohr.status === "beschaedigt" ? 3 : 1.5}
                        opacity={rb.rohr.status === "blockiert" ? 0.5 : 1}
                      />
                      {belegt && (
                        <circle r={7} fill="#ffffff" fillOpacity={0.85} />
                      )}
                      <text textAnchor="middle" dy={4} fontSize={10} fontWeight={600}
                            fill={belegt ? "#1e293b" : "#334155"}>
                        {rb.rohr.nummer}
                      </text>
                    </g>
                  );
                })}
              </svg>

              <div className="flex-1 min-w-[200px]">
                {hovered ? (
                  <div className="text-sm">
                    <p className="font-medium text-ink-900 dark:text-slate-100">Rohr {hovered.rohr.nummer} · {STATUS_LABEL[hovered.rohr.status]}</p>
                    <p className="text-slate-500">Durchmesser: {hovered.rohr.durchmesser_mm ?? "–"} mm · {hovered.rohr.typ ?? "–"}</p>
                    {hovered.kabel ? (
                      <div className="mt-2 space-y-0.5">
                        <p><span className="text-slate-400">Kabel:</span> {hovered.kabel.bezeichnung}</p>
                        <p><span className="text-slate-400">Typ:</span> {hovered.kabel.typ}</p>
                        <p><span className="text-slate-400">Fasern:</span> {hovered.kabel.belegte_fasern}/{hovered.kabel.fasernanzahl ?? "–"} belegt</p>
                      </div>
                    ) : (
                      <p className="text-signal-600 mt-2">Rohr ist frei</p>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-slate-400">
                    Rohr im Querschnitt auswählen für Details. {rv.rohre.filter((r) => r.kabel).length}/{rv.rohre.length} Rohre belegt.
                  </div>
                )}
              </div>
            </div>

            {/* Lineare Belegungsdarstellung entlang der Trasse */}
            <div className="mt-4">
              <p className="text-xs text-ink-400 mb-1">Belegung entlang der Trasse</p>
              <div className="space-y-1">
                {rv.rohre.map((rb) => (
                  <div key={rb.rohr.id} className="flex items-center gap-2 text-xs">
                    <span className="w-14 text-slate-500">Rohr {rb.rohr.nummer}</span>
                    <div className="flex-1 h-3 rounded bg-slate-100 dark:bg-slate-700 relative overflow-hidden">
                      {rb.kabel && (
                        <div
                          className="absolute top-0 bottom-0 rounded"
                          style={{
                            left: 0,
                            right: 0,
                            backgroundColor: rb.rohr.farbe,
                            opacity: 0.85,
                          }}
                          title={rb.kabel.bezeichnung}
                        />
                      )}
                    </div>
                    <span className="w-24 truncate text-slate-500">{rb.kabel?.bezeichnung ?? "frei"}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      })}

      {selected && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 animate-fade-in" onClick={() => setSelected(null)}>
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 w-96 shadow-2xl animate-modal-in" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold text-lg mb-3">Rohr {selected.rohr.nummer} Details</h3>
            <dl className="text-sm space-y-1.5">
              <div className="flex justify-between"><dt className="text-slate-400">Status</dt><dd>{STATUS_LABEL[selected.rohr.status]}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Durchmesser</dt><dd>{selected.rohr.durchmesser_mm ?? "–"} mm</dd></div>
              <div className="flex justify-between"><dt className="text-ink-400">Typ</dt><dd>{selected.rohr.typ ?? "–"}</dd></div>
              {selected.kabel && (
                <>
                  <div className="flex justify-between"><dt className="text-ink-400">Kabel</dt><dd>{selected.kabel.bezeichnung}</dd></div>
                  <div className="flex justify-between"><dt className="text-ink-400">Kabeltyp</dt><dd>{selected.kabel.typ}</dd></div>
                  <div className="flex justify-between"><dt className="text-ink-400">Fasern</dt><dd>{selected.kabel.belegte_fasern}/{selected.kabel.fasernanzahl}</dd></div>
                  <div className="flex justify-between"><dt className="text-ink-400">Segment</dt><dd>{selected.segment_start_m ?? 0}–{selected.segment_ende_m ?? "?"} m</dd></div>
                </>
              )}
            </dl>

            {!selected.kabel && (selected.rohr.status === "frei") && canEdit && (
              <KabelEinziehenForm
                rohrId={selected.rohr.id}
                onCreated={() => { setSelected(null); reload(); }}
              />
            )}

            <button onClick={() => setSelected(null)} className="mt-3 w-full bg-paper-dim dark:bg-slate-700 rounded-lg py-2 text-sm">Schließen</button>
          </div>
        </div>
      )}
    </div>
  );
}

function KabelEinziehenForm({ rohrId, onCreated }: { rohrId: string; onCreated: () => void }) {
  const [form, setForm] = useState({ bezeichnung: "", typ: "glasfaser", fasernanzahl: "24", hersteller: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await editApi.createKabel({
        bezeichnung: form.bezeichnung, typ: form.typ,
        fasernanzahl: form.fasernanzahl ? Number(form.fasernanzahl) : null,
        hersteller: form.hersteller || null, rohr_id: rohrId,
      });
      toast.success(`Kabel "${form.bezeichnung}" eingezogen.`);
      onCreated();
    } catch (err: any) {
      const msg = err.response?.data?.detail ?? "Kabel konnte nicht angelegt werden.";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 border-t border-ink-100 dark:border-slate-700 pt-3 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-ink-400">Kabel einziehen</p>
      {error && <p className="text-xs text-conduit-700 bg-conduit-50 rounded-md px-2 py-1.5">{error}</p>}
      <input required placeholder="Bezeichnung" value={form.bezeichnung}
             onChange={(e) => setForm({ ...form, bezeichnung: e.target.value })}
             className="w-full rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-2.5 py-1.5 text-sm" />
      <div className="grid grid-cols-2 gap-2">
        <select value={form.typ} onChange={(e) => setForm({ ...form, typ: e.target.value })}
                className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-2.5 py-1.5 text-sm">
          <option value="glasfaser">Glasfaser</option>
          <option value="kupfer">Kupfer</option>
        </select>
        <select value={form.fasernanzahl} onChange={(e) => setForm({ ...form, fasernanzahl: e.target.value })}
                className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-2.5 py-1.5 text-sm">
          {[12, 24, 48, 96, 144].map((n) => <option key={n} value={n}>{n} Fasern</option>)}
        </select>
      </div>
      <button type="submit" disabled={loading} className="w-full bg-ink-900 text-white rounded-md py-1.5 text-sm font-medium disabled:opacity-50">
        {loading ? "Speichert…" : "Kabel einziehen"}
      </button>
    </form>
  );
}

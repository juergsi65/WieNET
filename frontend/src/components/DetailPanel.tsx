import { useEffect, useState } from "react";
import { objektApi } from "../lib/api";
import RohrQuerschnitt from "./RohrQuerschnitt";
import { SkeletonLine } from "./Skeleton";

interface Props {
  typ: string;
  id: string;
  onClose: () => void;
  canEdit?: boolean;
}

const STATUS_BADGE: Record<string, string> = {
  aktiv: "bg-signal-100 text-signal-700",
  geplant: "bg-conduit-100 text-conduit-700",
  stillgelegt: "bg-slate-200 text-slate-500",
  gestoert: "bg-conduit-100 text-conduit-700",
};

export default function DetailPanel({ typ, id, onClose, canEdit = false }: Props) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showRohrbelegung, setShowRohrbelegung] = useState(false);

  useEffect(() => {
    setLoading(true);
    setShowRohrbelegung(false);
    objektApi.detail(typ, id).then((res) => setData(res.data)).finally(() => setLoading(false));
  }, [typ, id]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <aside className="w-96 shrink-0 h-full bg-white dark:bg-slate-800 border-l border-ink-100 dark:border-slate-700 overflow-y-auto animate-panel-in">
      <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-ink-100 dark:border-slate-700 p-4 flex items-center justify-between">
        <h3 className="font-display font-semibold text-ink-900 dark:text-slate-100">Objektdetails</h3>
        <button onClick={onClose} className="text-ink-400 hover:text-ink-600 text-xl leading-none w-7 h-7 rounded-md hover:bg-paper-dim dark:hover:bg-slate-700 transition flex items-center justify-center" title="Schließen (Esc)">×</button>
      </div>

      {loading && (
        <div className="p-4 space-y-3">
          <SkeletonLine width="70%" height="1.25rem" />
          <SkeletonLine width="40%" height="0.75rem" />
          <div className="grid grid-cols-2 gap-2 pt-2">
            <SkeletonLine height="0.85rem" />
            <SkeletonLine height="0.85rem" />
            <SkeletonLine height="0.85rem" />
            <SkeletonLine height="0.85rem" />
          </div>
        </div>
      )}

      {!loading && data && (
        <div className="p-4 space-y-4">
          <div>
            <h4 className="text-lg font-semibold text-ink-900 dark:text-slate-100">{data.name}</h4>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-xs uppercase tracking-wide text-ink-400">{data.typ}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[data.status] ?? "bg-slate-100"}`}>
                {data.status}
              </span>
              {data.ist_planung ? (
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-conduit-500 text-white">
                  ● Planung{data.erstellt_von ? ` von ${data.erstellt_von}` : ""}
                </span>
              ) : data.status === "aktiv" ? (
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-signal-600 text-white">
                  ● Live-Daten
                </span>
              ) : null}
            </div>
          </div>

          <dl className="text-sm grid grid-cols-2 gap-y-1.5">
            {data.laenge_m != null && (<><dt className="text-slate-400">Länge</dt><dd>{data.laenge_m} m</dd></>)}
            {data.verlegetiefe_cm != null && (<><dt className="text-slate-400">Verlegetiefe</dt><dd>{data.verlegetiefe_cm} cm</dd></>)}
            {data.oberflaeche && (<><dt className="text-slate-400">Oberfläche</dt><dd>{data.oberflaeche}</dd></>)}
            {data.adresse && (<><dt className="text-slate-400">Adresse</dt><dd>{data.adresse}</dd></>)}
            {data.gemeinde && (<><dt className="text-slate-400">Gemeinde</dt><dd>{data.gemeinde}</dd></>)}
            {data.baujahr && (<><dt className="text-slate-400">Baujahr</dt><dd>{data.baujahr}</dd></>)}
            {data.betreiber && (<><dt className="text-slate-400">Betreiber</dt><dd>{data.betreiber}</dd></>)}
            {data.eigentuemer && (<><dt className="text-slate-400">Eigentümer</dt><dd>{data.eigentuemer}</dd></>)}
            {data.hersteller && (<><dt className="text-slate-400">Hersteller</dt><dd>{data.hersteller}</dd></>)}
            {data.ports_gesamt != null && (
              <><dt className="text-slate-400">Ports belegt</dt><dd>{data.ports_belegt}/{data.ports_gesamt}</dd></>
            )}
          </dl>

          {data.notizen && (
            <div>
              <p className="text-xs text-ink-400 mb-1">Notizen</p>
              <p className="text-sm text-slate-600 dark:text-slate-300">{data.notizen}</p>
            </div>
          )}

          {typ === "trasse" && data.rohrverbaende?.length > 0 && (
            <div>
              <button
                onClick={() => setShowRohrbelegung((v) => !v)}
                className="w-full bg-brand-50 dark:bg-slate-700 text-brand-700 dark:text-brand-300 rounded-lg py-2 text-sm font-medium"
              >
                {showRohrbelegung ? "Rohrbelegung ausblenden" : "Rohrbelegung anzeigen"}
              </button>
              {showRohrbelegung && (
                <div className="mt-3">
                  <RohrQuerschnitt trasseId={id} canEdit={canEdit} />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </aside>
  );
}

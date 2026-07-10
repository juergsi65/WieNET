import { useEffect, useState } from "react";
import { objektApi } from "../lib/api";
import RohrQuerschnitt from "./RohrQuerschnitt";

interface Props {
  typ: string;
  id: string;
  onClose: () => void;
}

const STATUS_BADGE: Record<string, string> = {
  aktiv: "bg-green-100 text-green-700",
  geplant: "bg-slate-100 text-slate-600",
  stillgelegt: "bg-slate-200 text-slate-500",
  gestoert: "bg-red-100 text-red-700",
};

export default function DetailPanel({ typ, id, onClose }: Props) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showRohrbelegung, setShowRohrbelegung] = useState(false);

  useEffect(() => {
    setLoading(true);
    setShowRohrbelegung(false);
    objektApi.detail(typ, id).then((res) => setData(res.data)).finally(() => setLoading(false));
  }, [typ, id]);

  return (
    <aside className="w-96 shrink-0 h-full bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 overflow-y-auto">
      <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-4 flex items-center justify-between">
        <h3 className="font-semibold text-slate-800 dark:text-slate-100">Objektdetails</h3>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-xl leading-none">×</button>
      </div>

      {loading && <div className="p-4 text-sm text-slate-500">Wird geladen…</div>}

      {!loading && data && (
        <div className="p-4 space-y-4">
          <div>
            <h4 className="text-lg font-semibold text-slate-800 dark:text-slate-100">{data.name}</h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs uppercase tracking-wide text-slate-400">{data.typ}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[data.status] ?? "bg-slate-100"}`}>
                {data.status}
              </span>
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
              <p className="text-xs text-slate-400 mb-1">Notizen</p>
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
                  <RohrQuerschnitt trasseId={id} />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </aside>
  );
}

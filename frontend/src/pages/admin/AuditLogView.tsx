import { useEffect, useState } from "react";
import { adminAuditApi } from "../../lib/api";

const ERGEBNIS_FARBE: Record<string, string> = {
  erfolg: "bg-green-100 text-green-700",
  fehler: "bg-red-100 text-red-700",
  verweigert: "bg-amber-100 text-amber-700",
};

export default function AuditLogView() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [aktionFilter, setAktionFilter] = useState("");
  const pageSize = 30;

  function load() {
    adminAuditApi.list({ page, page_size: pageSize, aktion: aktionFilter || undefined }).then((res) => {
      setItems(res.data.items);
      setTotal(res.data.total);
    });
  }
  useEffect(load, [page, aktionFilter]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100">Audit-Log</h2>
        <input
          placeholder="Nach Aktion filtern (z.B. login, cluster_erstellt)"
          value={aktionFilter}
          onChange={(e) => { setAktionFilter(e.target.value); setPage(1); }}
          className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-1.5 text-sm w-72"
        />
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-x-auto">
        <table className="text-xs w-full">
          <thead className="bg-slate-50 dark:bg-slate-700 text-left">
            <tr>
              <th className="px-3 py-2">Zeitpunkt</th>
              <th className="px-3 py-2">Benutzer</th>
              <th className="px-3 py-2">Aktion</th>
              <th className="px-3 py-2">Objekt</th>
              <th className="px-3 py-2">IP</th>
              <th className="px-3 py-2">Ergebnis</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id} className="border-t border-slate-100 dark:border-slate-700">
                <td className="px-3 py-2 whitespace-nowrap">{new Date(it.zeitpunkt).toLocaleString("de-AT")}</td>
                <td className="px-3 py-2">{it.benutzer_name ?? "System"}</td>
                <td className="px-3 py-2 font-medium">{it.aktion}</td>
                <td className="px-3 py-2 text-slate-500">{it.objekt_typ ?? "–"}</td>
                <td className="px-3 py-2 text-slate-400">{it.ip_adresse ?? "–"}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded-full ${ERGEBNIS_FARBE[it.ergebnis] ?? "bg-slate-100"}`}>{it.ergebnis}</span>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={6} className="px-3 py-6 text-center text-slate-400">Keine Einträge gefunden.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-3 text-sm text-slate-500">
        <span>{total} Einträge gesamt</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-700 disabled:opacity-40">Zurück</button>
          <span>Seite {page} / {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} className="px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-700 disabled:opacity-40">Weiter</button>
        </div>
      </div>
    </div>
  );
}

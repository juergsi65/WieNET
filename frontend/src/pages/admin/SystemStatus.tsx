import { useEffect, useState } from "react";
import { adminSystemApi } from "../../lib/api";

function Row({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex justify-between py-2 border-b border-slate-100 dark:border-slate-700 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800 dark:text-slate-100">{value ?? "–"}</span>
    </div>
  );
}

export default function SystemStatus() {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    adminSystemApi.status().then((res) => setStatus(res.data));
  }, []);

  if (!status) return <div className="p-6 text-sm text-slate-500">Wird geladen…</div>;

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 mb-6">Systemstatus</h2>
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <Row label="Softwareversion" value={status.version} />
        <Row label="Frontend" value={status.frontend} />
        <Row label="API" value={status.api} />
        <Row label="Datenbank" value={status.datenbank} />
        <Row label="PostGIS-Version" value={status.postgis_version} />
        <Row label="Datenbankgröße" value={status.datenbankgroesse} />
        <Row label="Upload-Verzeichnis" value={status.upload_verzeichnis_mb ? `${status.upload_verzeichnis_mb} MB` : "–"} />
        <Row label="Datenträger frei" value={`${status.datenträger_frei_gb} GB / ${status.datenträger_gesamt_gb} GB`} />
        <Row label="Anzahl Benutzer" value={`${status.anzahl_aktive_benutzer} aktiv von ${status.anzahl_benutzer}`} />
        <Row label="Anzahl Objekte" value={status.anzahl_objekte} />
        {status.letzter_fehler && (
          <Row label="Letzter Fehler" value={`${status.letzter_fehler.aktion} (${new Date(status.letzter_fehler.zeitpunkt).toLocaleString("de-AT")})`} />
        )}
      </div>
    </div>
  );
}

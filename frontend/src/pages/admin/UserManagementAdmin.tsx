import { useEffect, useState } from "react";
import { adminUserApi, adminClusterApi } from "../../lib/api";

interface User {
  id: string; email: string; vorname: string | null; nachname: string | null;
  full_name: string; role: string; is_active: boolean; abteilung: string | null;
  letzter_login: string | null; fehlgeschlagene_logins: number;
}

const ROLES = [
  { value: "admin", label: "Administrator" },
  { value: "projektleiter", label: "Projektleiter" },
  { value: "planer", label: "Planer" },
  { value: "techniker", label: "Techniker" },
  { value: "betrachter", label: "Betrachter" },
];

const PERMISSIONS = [
  "daten_anzeigen", "daten_erstellen", "daten_bearbeiten", "daten_loeschen",
  "export_durchfuehren", "import_durchfuehren", "berichte_erstellen",
];

export default function UserManagementAdmin() {
  const [users, setUsers] = useState<User[]>([]);
  const [clusters, setClusters] = useState<any[]>([]);
  const [form, setForm] = useState({ email: "", vorname: "", nachname: "", password: "", role: "betrachter" });
  const [error, setError] = useState<string | null>(null);
  const [permissionUser, setPermissionUser] = useState<User | null>(null);
  const [tempPassword, setTempPassword] = useState<{ user: string; password: string } | null>(null);
  const [permForm, setPermForm] = useState({ scope_id: "", permission: "daten_anzeigen" });

  function load() {
    adminUserApi.list().then((res) => setUsers(res.data));
  }
  useEffect(() => {
    load();
    adminClusterApi.list({ with_geometry: false }).then((res) => setClusters(res.data));
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await adminUserApi.create({ ...form, muss_passwort_aendern: true });
      setForm({ email: "", vorname: "", nachname: "", password: "", role: "betrachter" });
      load();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Benutzer konnte nicht angelegt werden.");
    }
  }

  async function handleToggleActive(u: User) {
    if (u.is_active) await adminUserApi.deactivate(u.id);
    else await adminUserApi.reactivate(u.id);
    load();
  }

  async function handleGeneratePassword(u: User) {
    const res = await adminUserApi.generateTempPassword(u.id);
    setTempPassword({ user: u.full_name, password: res.data.temporaeres_passwort });
  }

  async function handleGrantPermission() {
    if (!permissionUser || !permForm.scope_id) return;
    await adminUserApi.grantPermission({
      user_id: permissionUser.id, scope_type: "cluster",
      scope_id: permForm.scope_id, permission: permForm.permission,
    });
    alert("Berechtigung vergeben.");
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 mb-6">Benutzerverwaltung</h2>

      {tempPassword && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm">
          Einmalpasswort für <strong>{tempPassword.user}</strong>: <code className="bg-white px-2 py-0.5 rounded">{tempPassword.password}</code>
          <button onClick={() => setTempPassword(null)} className="ml-3 text-amber-700 underline">Schließen</button>
        </div>
      )}

      <form onSubmit={handleCreate} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 mb-6 grid grid-cols-2 gap-3">
        <input required placeholder="Vorname" value={form.vorname} onChange={(e) => setForm({ ...form, vorname: e.target.value })}
               className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
        <input required placeholder="Nachname" value={form.nachname} onChange={(e) => setForm({ ...form, nachname: e.target.value })}
               className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
        <input required type="email" placeholder="E-Mail" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
               className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
        <input required type="password" placeholder="Initiales Passwort" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
               className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
          {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
        {error && <p className="col-span-2 text-sm text-red-600">{error}</p>}
        <button type="submit" className="col-span-2 bg-brand-600 text-white rounded-lg py-2 text-sm font-medium">Benutzer anlegen</button>
      </form>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
        {users.map((u) => (
          <div key={u.id} className="px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                  {u.full_name} <span className="text-slate-400 font-normal">· {u.email}</span>
                </p>
                <p className="text-xs text-slate-400">
                  {ROLES.find((r) => r.value === u.role)?.label} {!u.is_active && "· deaktiviert"}
                  {u.letzter_login && ` · letzter Login: ${new Date(u.letzter_login).toLocaleString("de-AT")}`}
                  {u.fehlgeschlagene_logins > 0 && ` · ${u.fehlgeschlagene_logins} fehlgeschlagene Logins`}
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <button onClick={() => setPermissionUser(permissionUser?.id === u.id ? null : u)} className="text-brand-600 hover:underline">
                  Cluster-Rechte
                </button>
                <button onClick={() => handleGeneratePassword(u)} className="text-slate-500 hover:underline">
                  Passwort zurücksetzen
                </button>
                <button onClick={() => handleToggleActive(u)} className={u.is_active ? "text-red-500 hover:underline" : "text-green-600 hover:underline"}>
                  {u.is_active ? "Deaktivieren" : "Reaktivieren"}
                </button>
              </div>
            </div>

            {permissionUser?.id === u.id && (
              <div className="mt-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3 flex items-center gap-2 text-xs">
                <select value={permForm.scope_id} onChange={(e) => setPermForm({ ...permForm, scope_id: e.target.value })}
                        className="rounded-md border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-2 py-1.5">
                  <option value="">Cluster wählen…</option>
                  {clusters.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
                <select value={permForm.permission} onChange={(e) => setPermForm({ ...permForm, permission: e.target.value })}
                        className="rounded-md border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-2 py-1.5">
                  {PERMISSIONS.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
                <button onClick={handleGrantPermission} className="bg-brand-600 text-white rounded-md px-3 py-1.5">Vergeben</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

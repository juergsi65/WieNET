import { useEffect, useState } from "react";
import { adminUserApi, adminClusterApi } from "../../lib/api";
import { toast } from "../../store/useToastStore";
import { confirmDialog } from "../../store/useConfirmStore";
import { SkeletonList } from "../../components/Skeleton";

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
  const [users, setUsers] = useState<User[] | null>(null);
  const [clusters, setClusters] = useState<any[]>([]);
  const [form, setForm] = useState({ email: "", vorname: "", nachname: "", password: "", role: "betrachter" });
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [permissionUser, setPermissionUser] = useState<User | null>(null);
  const [tempPassword, setTempPassword] = useState<{ user: string; password: string } | null>(null);
  const [permForm, setPermForm] = useState({ scope_id: "", permission: "daten_anzeigen" });
  const [grantingPermission, setGrantingPermission] = useState(false);
  const [busyUserId, setBusyUserId] = useState<string | null>(null);

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
    setCreating(true);
    try {
      await adminUserApi.create({ ...form, muss_passwort_aendern: true });
      setForm({ email: "", vorname: "", nachname: "", password: "", role: "betrachter" });
      load();
      toast.success(`Benutzer ${form.vorname} ${form.nachname} wurde angelegt.`);
    } catch (e: any) {
      const msg = e.response?.data?.detail ?? "Benutzer konnte nicht angelegt werden.";
      setError(msg);
      toast.error(msg);
    } finally {
      setCreating(false);
    }
  }

  async function handleToggleActive(u: User) {
    const willDeactivate = u.is_active;
    if (willDeactivate) {
      const ok = await confirmDialog(
        `${u.full_name} deaktivieren?`,
        "Der Benutzer kann sich danach nicht mehr anmelden, bis er reaktiviert wird.",
        true
      );
      if (!ok) return;
    }
    setBusyUserId(u.id);
    try {
      if (willDeactivate) await adminUserApi.deactivate(u.id);
      else await adminUserApi.reactivate(u.id);
      load();
      toast.success(willDeactivate ? `${u.full_name} wurde deaktiviert.` : `${u.full_name} wurde reaktiviert.`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Aktion fehlgeschlagen.");
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleGeneratePassword(u: User) {
    const ok = await confirmDialog(
      "Neues Einmalpasswort erzeugen?",
      `${u.full_name} muss sich beim nächsten Login mit einem neuen Passwort anmelden. Das alte Passwort wird ungültig.`
    );
    if (!ok) return;
    setBusyUserId(u.id);
    try {
      const res = await adminUserApi.generateTempPassword(u.id);
      setTempPassword({ user: u.full_name, password: res.data.temporaeres_passwort });
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Passwort konnte nicht erzeugt werden.");
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleGrantPermission() {
    if (!permissionUser || !permForm.scope_id) {
      toast.error("Bitte zuerst ein Cluster auswählen.");
      return;
    }
    setGrantingPermission(true);
    try {
      await adminUserApi.grantPermission({
        user_id: permissionUser.id, scope_type: "cluster",
        scope_id: permForm.scope_id, permission: permForm.permission,
      });
      toast.success("Berechtigung vergeben.");
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? "Berechtigung konnte nicht vergeben werden.");
    } finally {
      setGrantingPermission(false);
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="font-display text-xl font-semibold text-ink-900 dark:text-slate-100 mb-6">Benutzerverwaltung</h2>

      {tempPassword && (
        <div className="mb-4 bg-conduit-50 border border-conduit-100 rounded-lg p-3 text-sm animate-fade-in">
          Einmalpasswort für <strong>{tempPassword.user}</strong>:{" "}
          <code className="bg-white px-2 py-0.5 rounded font-data">{tempPassword.password}</code>
          <button onClick={() => setTempPassword(null)} className="ml-3 text-conduit-700 underline">Schließen</button>
        </div>
      )}

      <form onSubmit={handleCreate} className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 p-4 mb-6 grid grid-cols-2 gap-3">
        <input required placeholder="Vorname" value={form.vorname} onChange={(e) => setForm({ ...form, vorname: e.target.value })}
               className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm focus:ring-2 focus:ring-conduit-500 focus:border-conduit-500 outline-none transition" />
        <input required placeholder="Nachname" value={form.nachname} onChange={(e) => setForm({ ...form, nachname: e.target.value })}
               className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm focus:ring-2 focus:ring-conduit-500 focus:border-conduit-500 outline-none transition" />
        <input required type="email" placeholder="E-Mail" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
               className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm focus:ring-2 focus:ring-conduit-500 focus:border-conduit-500 outline-none transition" />
        <input required type="password" placeholder="Initiales Passwort" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
               className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm focus:ring-2 focus:ring-conduit-500 focus:border-conduit-500 outline-none transition" />
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm">
          {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
        {error && <p className="col-span-2 text-sm text-conduit-700 bg-conduit-50 rounded-md px-3 py-2">{error}</p>}
        <button type="submit" disabled={creating} className="col-span-2 bg-ink-900 hover:bg-blueprint text-white rounded-md py-2 text-sm font-medium transition disabled:opacity-50">
          {creating ? "Wird angelegt…" : "Benutzer anlegen"}
        </button>
      </form>

      {users === null ? (
        <SkeletonList count={4} />
      ) : (
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-ink-100 dark:border-slate-700 divide-y divide-ink-100 dark:divide-slate-700">
          {users.map((u) => (
            <div key={u.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-ink-900 dark:text-slate-100">
                    {u.full_name} <span className="text-ink-400 font-normal">· {u.email}</span>
                  </p>
                  <p className="text-xs text-ink-400">
                    {ROLES.find((r) => r.value === u.role)?.label} {!u.is_active && "· deaktiviert"}
                    {u.letzter_login && ` · letzter Login: ${new Date(u.letzter_login).toLocaleString("de-AT")}`}
                    {u.fehlgeschlagene_logins > 0 && ` · ${u.fehlgeschlagene_logins} fehlgeschlagene Logins`}
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <button onClick={() => setPermissionUser(permissionUser?.id === u.id ? null : u)} className="text-signal-600 hover:underline">
                    Cluster-Rechte
                  </button>
                  <button onClick={() => handleGeneratePassword(u)} disabled={busyUserId === u.id} className="text-ink-400 hover:underline disabled:opacity-50">
                    Passwort zurücksetzen
                  </button>
                  <button
                    onClick={() => handleToggleActive(u)}
                    disabled={busyUserId === u.id}
                    className={`${u.is_active ? "text-conduit-600" : "text-signal-600"} hover:underline disabled:opacity-50`}
                  >
                    {busyUserId === u.id ? "…" : u.is_active ? "Deaktivieren" : "Reaktivieren"}
                  </button>
                </div>
              </div>

              {permissionUser?.id === u.id && (
                <div className="mt-3 bg-paper-dim dark:bg-slate-700/50 rounded-lg p-3 flex items-center gap-2 text-xs animate-fade-in">
                  <select value={permForm.scope_id} onChange={(e) => setPermForm({ ...permForm, scope_id: e.target.value })}
                          className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-2 py-1.5">
                    <option value="">Cluster wählen…</option>
                    {clusters.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                  <select value={permForm.permission} onChange={(e) => setPermForm({ ...permForm, permission: e.target.value })}
                          className="rounded-md border border-ink-100 dark:border-slate-600 dark:bg-slate-700 px-2 py-1.5">
                    {PERMISSIONS.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                  <button onClick={handleGrantPermission} disabled={grantingPermission} className="bg-ink-900 text-white rounded-md px-3 py-1.5 disabled:opacity-50">
                    {grantingPermission ? "…" : "Vergeben"}
                  </button>
                </div>
              )}
            </div>
          ))}
          {users.length === 0 && <p className="p-4 text-sm text-ink-400">Noch keine weiteren Benutzer angelegt.</p>}
        </div>
      )}
    </div>
  );
}

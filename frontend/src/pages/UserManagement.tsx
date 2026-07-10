import { useEffect, useState } from "react";
import { api } from "../lib/api";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

const ROLES = [
  { value: "admin", label: "Administrator" },
  { value: "planer", label: "Planer" },
  { value: "techniker", label: "Techniker" },
  { value: "betrachter", label: "Betrachter" },
];

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role: "betrachter" });
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get("/users").then((res) => setUsers(res.data));
  }

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/users", form);
      setForm({ email: "", full_name: "", password: "", role: "betrachter" });
      load();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? "Benutzer konnte nicht angelegt werden.");
    }
  }

  async function handleDeactivate(id: string) {
    await api.delete(`/users/${id}`);
    load();
  }

  return (
    <div className="p-6 max-w-3xl mx-auto overflow-y-auto h-full">
      <h2 className="text-xl font-semibold text-slate-800 dark:text-slate-100 mb-6">Benutzerverwaltung</h2>

      <form onSubmit={handleCreate} className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4 mb-6 grid grid-cols-2 gap-3">
        <input required placeholder="Name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
               className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
        <input required type="email" placeholder="E-Mail" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
               className="rounded-lg border border-slate-300 dark:border-slate-600 dark:bg-slate-700 px-3 py-2 text-sm" />
        <input required type="password" placeholder="Passwort" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
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
          <div key={u.id} className="flex items-center justify-between px-4 py-3">
            <div>
              <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{u.full_name} <span className="text-slate-400 font-normal">· {u.email}</span></p>
              <p className="text-xs text-slate-400">{ROLES.find((r) => r.value === u.role)?.label} {!u.is_active && "· deaktiviert"}</p>
            </div>
            {u.is_active && (
              <button onClick={() => handleDeactivate(u.id)} className="text-xs text-red-500 hover:underline">Deaktivieren</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

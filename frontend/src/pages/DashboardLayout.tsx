import { useState } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { useAppStore } from "../store/useAppStore";
import Sidebar from "../components/Sidebar";
import DetailPanel from "../components/DetailPanel";
import MapView from "../components/MapView";
import Netzschema from "../components/Netzschema";
import DashboardHome from "./DashboardHome";
import ImportWizard from "./ImportWizard";
import AdminLayout from "./admin/AdminLayout";

const NAV_ITEMS = [
  { path: "/", label: "Karte" },
  { path: "/netzschema", label: "Netzschema" },
  { path: "/dashboard", label: "Dashboard" },
  { path: "/import", label: "Import" },
];

export default function DashboardLayout() {
  const [selected, setSelected] = useState<{ typ: string; id: string } | null>(null);
  const darkMode = useAppStore((s) => s.darkMode);
  const toggleDarkMode = useAppStore((s) => s.toggleDarkMode);
  const role = useAppStore((s) => s.role);
  const fullName = useAppStore((s) => s.fullName);
  const logout = useAppStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();

  function handleSelect(typ: string, id: string) {
    setSelected({ typ, id });
  }

  return (
    <div className={darkMode ? "dark" : ""}>
      <div className="h-screen w-screen flex flex-col bg-slate-50 dark:bg-slate-900">
        {/* Obere Navigationsleiste */}
        <header className="h-14 shrink-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center px-4 gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm">T</div>
            <span className="font-semibold text-slate-800 dark:text-slate-100 hidden sm:inline">Tiefbau-Infrastruktur</span>
          </div>
          <nav className="flex gap-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  location.pathname === item.path
                    ? "bg-brand-50 dark:bg-slate-700 text-brand-700 dark:text-brand-300"
                    : "text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700"
                }`}
              >
                {item.label}
              </button>
            ))}
            {role === "admin" && (
              <button
                onClick={() => navigate("/admin")}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  location.pathname.startsWith("/admin")
                    ? "bg-brand-50 dark:bg-slate-700 text-brand-700 dark:text-brand-300"
                    : "text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700"
                }`}
              >
                Administration
              </button>
            )}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <button onClick={toggleDarkMode} className="text-sm text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" title="Darstellung wechseln">
              {darkMode ? "☀️" : "🌙"}
            </button>
            <span className="text-sm text-slate-500 dark:text-slate-300 hidden md:inline">{fullName} · {role}</span>
            <button onClick={logout} className="text-sm text-slate-400 hover:text-red-600">Abmelden</button>
          </div>
        </header>

        {/* Hauptbereich */}
        <div className="flex-1 flex overflow-hidden">
          <Routes>
            <Route
              path="/"
              element={
                <>
                  <Sidebar onSelectSearchResult={(typ, id) => handleSelect(typ, id)} />
                  <main className="flex-1 relative">
                    <MapView onSelect={handleSelect} />
                  </main>
                  {selected && (
                    <DetailPanel typ={selected.typ} id={selected.id} onClose={() => setSelected(null)} />
                  )}
                </>
              }
            />
            <Route
              path="/netzschema"
              element={
                <>
                  <main className="flex-1 relative">
                    <Netzschema onSelectNode={(id, typ) => handleSelect(typ, id)} />
                  </main>
                  {selected && (
                    <DetailPanel typ={selected.typ} id={selected.id} onClose={() => setSelected(null)} />
                  )}
                </>
              }
            />
            <Route path="/dashboard" element={<main className="flex-1"><DashboardHome /></main>} />
            <Route path="/import" element={<main className="flex-1"><ImportWizard /></main>} />
            {role === "admin" && <Route path="/admin/*" element={<AdminLayout />} />}
          </Routes>
        </div>
      </div>
    </div>
  );
}

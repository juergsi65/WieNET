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
      <div className="h-screen w-screen flex flex-col bg-paper dark:bg-slate-900">
        {/* Obere Navigationsleiste - dunkles Blueprint-Design */}
        <header className="h-14 shrink-0 bg-blueprint flex items-center px-4 gap-6 shadow-panel z-10">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-conduit-500 flex items-center justify-center text-white font-display font-bold text-sm">W</div>
            <span className="font-display font-semibold text-paper hidden sm:inline tracking-tight">WieNet</span>
          </div>
          <nav className="flex gap-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                  location.pathname === item.path
                    ? "bg-white/10 text-white"
                    : "text-paper/60 hover:bg-white/5 hover:text-paper/90"
                }`}
              >
                {item.label}
              </button>
            ))}
            {role === "admin" && (
              <button
                onClick={() => navigate("/admin")}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                  location.pathname.startsWith("/admin")
                    ? "bg-conduit-500 text-white"
                    : "text-paper/60 hover:bg-white/5 hover:text-paper/90"
                }`}
              >
                Administration
              </button>
            )}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <button onClick={toggleDarkMode} className="text-sm text-paper/50 hover:text-paper transition" title="Darstellung wechseln">
              {darkMode ? "☀️" : "🌙"}
            </button>
            <span className="text-sm text-paper/60 hidden md:inline font-data">{fullName} · {role}</span>
            <button onClick={logout} className="text-sm text-paper/50 hover:text-conduit-300 transition">Abmelden</button>
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

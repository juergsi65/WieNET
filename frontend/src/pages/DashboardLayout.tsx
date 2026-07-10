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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const darkMode = useAppStore((s) => s.darkMode);
  const toggleDarkMode = useAppStore((s) => s.toggleDarkMode);
  const role = useAppStore((s) => s.role);
  const fullName = useAppStore((s) => s.fullName);
  const logout = useAppStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();
  const canEdit = ["admin", "projektleiter", "planer"].includes(role ?? "");

  function handleSelect(typ: string, id: string) {
    setSelected({ typ, id });
  }

  function handleNavigate(path: string) {
    navigate(path);
    setSidebarOpen(false);
  }

  return (
    <div className={darkMode ? "dark" : ""}>
      <div className="h-screen w-screen flex flex-col bg-paper dark:bg-slate-900">
        {/* Obere Navigationsleiste - dunkles Blueprint-Design */}
        <header className="h-14 shrink-0 bg-blueprint flex items-center px-4 gap-3 sm:gap-6 shadow-panel z-20">
          {/* Hamburger nur auf schmalen Bildschirmen (Tablet-Hochformat/Mobile) */}
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="md:hidden text-paper/70 hover:text-paper w-8 h-8 flex items-center justify-center rounded-md hover:bg-white/5 transition"
            aria-label="Menü"
          >
            ☰
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-conduit-500 flex items-center justify-center text-white font-display font-bold text-sm shrink-0">W</div>
            <span className="font-display font-semibold text-paper hidden sm:inline tracking-tight">WieNet</span>
          </div>

          <nav className="hidden md:flex gap-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.path}
                onClick={() => handleNavigate(item.path)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 ${
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
                onClick={() => handleNavigate("/admin")}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 ${
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

        {/* Mobile/Tablet-Navigation als Dropdown unter dem Header */}
        {sidebarOpen && (
          <nav className="md:hidden bg-blueprint-800 px-4 py-2 flex flex-col gap-1 animate-fade-in z-20">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.path}
                onClick={() => handleNavigate(item.path)}
                className={`text-left px-3 py-2 rounded-md text-sm font-medium ${
                  location.pathname === item.path ? "bg-white/10 text-white" : "text-paper/70"
                }`}
              >
                {item.label}
              </button>
            ))}
            {role === "admin" && (
              <button onClick={() => handleNavigate("/admin")} className="text-left px-3 py-2 rounded-md text-sm font-medium text-conduit-300">
                Administration
              </button>
            )}
          </nav>
        )}

        {/* Hauptbereich */}
        <div className="flex-1 flex overflow-hidden relative">
          <Routes>
            <Route
              path="/"
              element={
                <>
                  <div className="hidden md:block h-full">
                    <Sidebar onSelectSearchResult={(typ, id) => handleSelect(typ, id)} />
                  </div>
                  <main className="flex-1 relative">
                    <MapView onSelect={handleSelect} canEdit={canEdit} />
                  </main>
                  {selected && (
                    <div className="fixed md:relative inset-0 md:inset-auto z-30 md:z-auto">
                      <DetailPanel typ={selected.typ} id={selected.id} onClose={() => setSelected(null)} canEdit={canEdit} />
                    </div>
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
                    <div className="fixed md:relative inset-0 md:inset-auto z-30 md:z-auto">
                      <DetailPanel typ={selected.typ} id={selected.id} onClose={() => setSelected(null)} canEdit={canEdit} />
                    </div>
                  )}
                </>
              }
            />
            <Route path="/dashboard" element={<main className="flex-1 overflow-y-auto"><DashboardHome /></main>} />
            <Route path="/import" element={<main className="flex-1 overflow-y-auto"><ImportWizard /></main>} />
            {role === "admin" && <Route path="/admin/*" element={<AdminLayout />} />}
          </Routes>
        </div>
      </div>
    </div>
  );
}

import { NavLink, Routes, Route, Navigate } from "react-router-dom";
import AdminOverview from "./AdminOverview";
import AreaManagement from "./AreaManagement";
import ClusterManagement from "./ClusterManagement";
import ClusterDetail from "./ClusterDetail";
import ProjectManagement from "./ProjectManagement";
import ProjectDetail from "./ProjectDetail";
import UserManagementAdmin from "./UserManagementAdmin";
import AuditLogView from "./AuditLogView";
import SystemStatus from "./SystemStatus";
import MaterialCatalog from "./MaterialCatalog";
import NumberingManagement from "./NumberingManagement";

const NAV = [
  { path: "", label: "Übersicht", end: true },
  { path: "benutzer", label: "Benutzer" },
  { path: "gebiete", label: "Gebiete" },
  { path: "cluster", label: "Cluster" },
  { path: "projekte", label: "Projekte" },
  { path: "materialkatalog", label: "Materialkatalog" },
  { path: "nummernkreise", label: "Nummernkreise" },
  { path: "audit-log", label: "Audit-Log" },
  { path: "systemstatus", label: "Systemstatus" },
];

export default function AdminLayout() {
  return (
    <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
      {/* Ab Tablet-Breite (lg) klassische vertikale Sidebar; darunter horizontale Scroll-Leiste */}
      <aside className="shrink-0 bg-white dark:bg-slate-800 border-b lg:border-b-0 lg:border-r border-ink-100 dark:border-slate-700 p-3 lg:w-56 lg:h-full">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-400 px-2 mb-2 hidden lg:block">Administration</p>
        <nav className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible pb-1 lg:pb-0">
          {NAV.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `whitespace-nowrap px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? "bg-conduit-50 dark:bg-slate-700 text-conduit-700 dark:text-conduit-300"
                    : "text-ink-600 dark:text-slate-300 hover:bg-paper-dim dark:hover:bg-slate-700"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto animate-fade-in">
        <Routes>
          <Route index element={<AdminOverview />} />
          <Route path="benutzer" element={<UserManagementAdmin />} />
          <Route path="gebiete" element={<AreaManagement />} />
          <Route path="cluster" element={<ClusterManagement />} />
          <Route path="cluster/:clusterId" element={<ClusterDetail />} />
          <Route path="projekte" element={<ProjectManagement />} />
          <Route path="projekte/:projectId" element={<ProjectDetail />} />
          <Route path="materialkatalog" element={<MaterialCatalog />} />
          <Route path="nummernkreise" element={<NumberingManagement />} />
          <Route path="audit-log" element={<AuditLogView />} />
          <Route path="systemstatus" element={<SystemStatus />} />
          <Route path="*" element={<Navigate to="" replace />} />
        </Routes>
      </main>
    </div>
  );
}

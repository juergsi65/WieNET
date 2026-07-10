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

const NAV = [
  { path: "", label: "Übersicht", end: true },
  { path: "benutzer", label: "Benutzer" },
  { path: "gebiete", label: "Gebiete" },
  { path: "cluster", label: "Cluster" },
  { path: "projekte", label: "Projekte" },
  { path: "audit-log", label: "Audit-Log" },
  { path: "systemstatus", label: "Systemstatus" },
];

export default function AdminLayout() {
  return (
    <div className="flex-1 flex overflow-hidden">
      <aside className="w-56 shrink-0 h-full bg-white dark:bg-slate-800 border-r border-ink-100 dark:border-slate-700 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-400 px-2 mb-2">Administration</p>
        <nav className="space-y-1">
          {NAV.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm font-medium ${
                  isActive
                    ? "bg-brand-50 dark:bg-slate-700 text-brand-700 dark:text-brand-300"
                    : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route index element={<AdminOverview />} />
          <Route path="benutzer" element={<UserManagementAdmin />} />
          <Route path="gebiete" element={<AreaManagement />} />
          <Route path="cluster" element={<ClusterManagement />} />
          <Route path="cluster/:clusterId" element={<ClusterDetail />} />
          <Route path="projekte" element={<ProjectManagement />} />
          <Route path="projekte/:projectId" element={<ProjectDetail />} />
          <Route path="audit-log" element={<AuditLogView />} />
          <Route path="systemstatus" element={<SystemStatus />} />
          <Route path="*" element={<Navigate to="" replace />} />
        </Routes>
      </main>
    </div>
  );
}

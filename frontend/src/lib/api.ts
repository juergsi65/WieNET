import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("tiefbau_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("tiefbau_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: any[];
}

export const mapApi = {
  trassen: (zoom: number, bbox?: string, statusFilter?: string) =>
    api.get<GeoJSONFeatureCollection>("/map/trassen", { params: { zoom, bbox, status_filter: statusFilter } }),
  netzelemente: (zoom: number, bbox?: string, statusFilter?: string) =>
    api.get<GeoJSONFeatureCollection>("/map/netzelemente", { params: { zoom, bbox, status_filter: statusFilter } }),
};

export const objektApi = {
  detail: (typ: string, id: string) => api.get(`/objekt/${typ}/${id}`),
  search: (q: string) => api.get("/search", { params: { q } }),
  dashboard: () => api.get("/dashboard"),
};

export const rohrbelegungApi = {
  fuerTrasse: (trasseId: string) => api.get(`/rohrbelegung/trasse/${trasseId}`),
  fuerRohrverband: (id: string) => api.get(`/rohrbelegung/rohrverband/${id}`),
};

export const netzschemaApi = {
  baum: () => api.get("/netzschema/baum"),
  pfad: (id: string) => api.get(`/netzschema/pfad/${id}`),
};

export const authApi = {
  login: (email: string, password: string) => api.post("/auth/login", { email, password }),
  me: () => api.get("/auth/me"),
};

// --- Admin: Gebiete, Cluster, Projekte, Bauabschnitte ---

export const adminAreaApi = {
  list: (withGeometry = false) => api.get("/admin/areas", { params: { with_geometry: withGeometry } }),
  get: (id: string) => api.get(`/admin/areas/${id}`),
  create: (payload: any) => api.post("/admin/areas", payload),
  update: (id: string, payload: any) => api.patch(`/admin/areas/${id}`, payload),
  remove: (id: string) => api.delete(`/admin/areas/${id}`),
};

export const adminClusterApi = {
  list: (params?: { project_id?: string; gebiet_id?: string; with_geometry?: boolean }) =>
    api.get("/admin/clusters", { params }),
  get: (id: string) => api.get(`/admin/clusters/${id}`),
  create: (payload: any) => api.post("/admin/clusters", payload),
  update: (id: string, payload: any) => api.patch(`/admin/clusters/${id}`, payload),
  remove: (id: string) => api.delete(`/admin/clusters/${id}`),
  stats: (id: string) => api.get(`/admin/clusters/${id}/stats`),
  zuordnungVorschau: (id: string) => api.get(`/admin/clusters/${id}/zuordnung/vorschau`),
  zuordnungBestaetigen: (id: string, objekt_typen: string[]) =>
    api.post(`/admin/clusters/${id}/zuordnung/bestaetigen`, { objekt_typen }),
  mergeVorschau: (cluster_ids: string[]) => api.post("/admin/clusters/merge/vorschau", { cluster_ids }),
  merge: (payload: { cluster_ids: string[]; name: string; kuerzel?: string; gebiet_id?: string | null; project_id?: string | null; farbe?: string }) =>
    api.post("/admin/clusters/merge", payload),
};

export const numberingApi = {
  list: (entity_type?: string) => api.get("/admin/nummernschemata", { params: { entity_type } }),
  create: (payload: { entity_type: string; name: string; pattern: string; scope: string; start_value: number }) =>
    api.post("/admin/nummernschemata", payload),
  activate: (id: string) => api.post(`/admin/nummernschemata/${id}/aktivieren`),
  remove: (id: string) => api.delete(`/admin/nummernschemata/${id}`),
  vorschau: (entity_type: string, params?: { gebiet_id?: string; cluster_id?: string; projekt_id?: string }) =>
    api.get(`/admin/nummernschemata/vorschau/${entity_type}`, { params }),
};

export const adminProjectApi = {
  list: (statusFilter?: string) => api.get("/admin/projects", { params: { status_filter: statusFilter } }),
  get: (id: string) => api.get(`/admin/projects/${id}`),
  create: (payload: any) => api.post("/admin/projects", payload),
  dashboard: (id: string) => api.get(`/admin/projects/${id}/dashboard`),
};

export const adminBauabschnittApi = {
  list: (params?: { project_id?: string; cluster_id?: string }) =>
    api.get("/admin/construction-sections", { params }),
  create: (payload: any) => api.post("/admin/construction-sections", payload),
  update: (id: string, params: { fortschritt_pct?: number; status_neu?: string }) =>
    api.patch(`/admin/construction-sections/${id}`, null, { params }),
};

export const adminUserApi = {
  list: () => api.get("/admin/users"),
  create: (payload: any) => api.post("/admin/users", payload),
  update: (id: string, payload: any) => api.patch(`/admin/users/${id}`, payload),
  deactivate: (id: string) => api.post(`/admin/users/${id}/deaktivieren`),
  reactivate: (id: string) => api.post(`/admin/users/${id}/reaktivieren`),
  remove: (id: string) => api.delete(`/admin/users/${id}`),
  resetPassword: (id: string, new_password: string, muss_passwort_aendern = true) =>
    api.post(`/admin/users/${id}/passwort-zuruecksetzen`, { new_password, muss_passwort_aendern }),
  generateTempPassword: (id: string) => api.post(`/admin/users/${id}/generiere-passwort`),
  getPermissions: (id: string) => api.get(`/admin/users/${id}/berechtigungen`),
  grantPermission: (payload: { user_id: string; scope_type: string; scope_id: string; permission: string }) =>
    api.post("/admin/users/berechtigungen/vergeben", payload),
  revokePermission: (payload: { user_id: string; scope_type: string; scope_id: string; permission: string }) =>
    api.post("/admin/users/berechtigungen/entziehen", payload),
};

export const adminAuditApi = {
  list: (params: Record<string, any>) => api.get("/admin/audit-log", { params }),
};

export const adminSystemApi = {
  status: () => api.get("/admin/system/status"),
};

// --- Admin: Materialkatalog (Hersteller, Produkte, Farben, Rohrverband-/Kabelvorlagen) ---

export const materialApi = {
  hersteller: {
    list: (nurAktive = false) => api.get("/admin/materialkatalog/hersteller", { params: { nur_aktive: nurAktive } }),
    create: (payload: any) => api.post("/admin/materialkatalog/hersteller", payload),
    update: (id: string, payload: any) => api.patch(`/admin/materialkatalog/hersteller/${id}`, payload),
    remove: (id: string) => api.delete(`/admin/materialkatalog/hersteller/${id}`),
  },
  kategorien: {
    list: () => api.get("/admin/materialkatalog/kategorien"),
    create: (payload: any) => api.post("/admin/materialkatalog/kategorien", payload),
    remove: (id: string) => api.delete(`/admin/materialkatalog/kategorien/${id}`),
  },
  farben: {
    list: (farbstandard?: string) => api.get("/admin/materialkatalog/farben", { params: { farbstandard } }),
    create: (payload: any) => api.post("/admin/materialkatalog/farben", payload),
    remove: (id: string) => api.delete(`/admin/materialkatalog/farben/${id}`),
  },
  produktfamilien: {
    list: (params?: { hersteller_id?: string; kategorie_id?: string }) => api.get("/admin/materialkatalog/produktfamilien", { params }),
    create: (payload: any) => api.post("/admin/materialkatalog/produktfamilien", payload),
    remove: (id: string) => api.delete(`/admin/materialkatalog/produktfamilien/${id}`),
  },
  produkte: {
    list: (params?: { produktfamilie_id?: string; produkttyp?: string; nur_aktive?: boolean }) => api.get("/admin/materialkatalog/produkte", { params }),
    create: (payload: any) => api.post("/admin/materialkatalog/produkte", payload),
    update: (id: string, payload: any) => api.patch(`/admin/materialkatalog/produkte/${id}`, payload),
    remove: (id: string) => api.delete(`/admin/materialkatalog/produkte/${id}`),
  },
  rohrverbandVorlagen: {
    list: (nurAktive = false) => api.get("/admin/materialkatalog/rohrverband-vorlagen", { params: { nur_aktive: nurAktive } }),
    create: (payload: any) => api.post("/admin/materialkatalog/rohrverband-vorlagen", payload),
    remove: (id: string) => api.delete(`/admin/materialkatalog/rohrverband-vorlagen/${id}`),
  },
  kabelVorlagen: {
    list: (nurAktive = false) => api.get("/admin/materialkatalog/kabel-vorlagen", { params: { nur_aktive: nurAktive } }),
    create: (payload: any) => api.post("/admin/materialkatalog/kabel-vorlagen", payload),
    remove: (id: string) => api.delete(`/admin/materialkatalog/kabel-vorlagen/${id}`),
  },
};

// --- Redlining: Trassen, Netzelemente, Kabel direkt anlegen ---

export const editApi = {
  referenzdaten: () => api.get("/edit/referenzdaten"),
  createTrasse: (payload: any) => api.post("/edit/trasse", payload),
  createNetzelement: (payload: any) => api.post("/edit/netzelement", payload),
  createKabel: (payload: any) => api.post("/edit/kabel", payload),
};

import { create } from "zustand";

interface SelectedObject {
  typ: string;
  id: string;
}

interface AppState {
  token: string | null;
  role: string | null;
  fullName: string | null;
  darkMode: boolean;
  selectedObject: SelectedObject | null;
  activeLayers: Record<string, boolean>;
  datenFilter: "alle" | "live" | "planung";
  setAuth: (token: string, role: string, fullName: string) => void;
  logout: () => void;
  toggleDarkMode: () => void;
  selectObject: (obj: SelectedObject | null) => void;
  toggleLayer: (layer: string) => void;
  setDatenFilter: (filter: "alle" | "live" | "planung") => void;
}

export const useAppStore = create<AppState>((set) => ({
  token: localStorage.getItem("tiefbau_token"),
  role: localStorage.getItem("tiefbau_role"),
  fullName: localStorage.getItem("tiefbau_name"),
  darkMode: localStorage.getItem("tiefbau_dark") === "1",
  selectedObject: null,
  datenFilter: "alle",
  activeLayers: {
    trassen: true, schacht: true, muffe: true, verteiler: true,
    fcp: true, olt: true, pon: true, hausanschluss: true, cluster: true,
  },
  setAuth: (token, role, fullName) => {
    localStorage.setItem("tiefbau_token", token);
    localStorage.setItem("tiefbau_role", role);
    localStorage.setItem("tiefbau_name", fullName);
    set({ token, role, fullName });
  },
  logout: () => {
    localStorage.removeItem("tiefbau_token");
    localStorage.removeItem("tiefbau_role");
    localStorage.removeItem("tiefbau_name");
    set({ token: null, role: null, fullName: null });
  },
  toggleDarkMode: () =>
    set((s) => {
      const next = !s.darkMode;
      localStorage.setItem("tiefbau_dark", next ? "1" : "0");
      return { darkMode: next };
    }),
  selectObject: (obj) => set({ selectedObject: obj }),
  setDatenFilter: (filter) => set({ datenFilter: filter }),
  toggleLayer: (layer) =>
    set((s) => ({ activeLayers: { ...s.activeLayers, [layer]: !s.activeLayers[layer] } })),
}));

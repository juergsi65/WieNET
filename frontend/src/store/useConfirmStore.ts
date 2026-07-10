import { create } from "zustand";

interface ConfirmState {
  open: boolean;
  title: string;
  message: string;
  danger: boolean;
  resolve: ((value: boolean) => void) | null;
  request: (title: string, message: string, danger?: boolean) => Promise<boolean>;
  handle: (value: boolean) => void;
}

export const useConfirmStore = create<ConfirmState>((set, get) => ({
  open: false,
  title: "",
  message: "",
  danger: false,
  resolve: null,
  request: (title, message, danger = false) => {
    return new Promise<boolean>((resolve) => {
      set({ open: true, title, message, danger, resolve });
    });
  },
  handle: (value) => {
    const { resolve } = get();
    set({ open: false, resolve: null });
    resolve?.(value);
  },
}));

/** Praktische Ersatzfunktion für window.confirm(): `if (await confirmDialog("Titel", "Text")) { ... }` */
export function confirmDialog(title: string, message: string, danger = false) {
  return useConfirmStore.getState().request(title, message, danger);
}

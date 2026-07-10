import { useEffect, useRef } from "react";
import { useConfirmStore } from "../store/useConfirmStore";

export default function ConfirmDialog() {
  const { open, title, message, danger, handle } = useConfirmStore();
  const confirmBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) confirmBtnRef.current?.focus();
  }, [open]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!open) return;
      if (e.key === "Escape") handle(false);
      if (e.key === "Enter") handle(true);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, handle]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-[110] animate-fade-in" onClick={() => handle(false)}>
      <div
        className="bg-white dark:bg-slate-800 rounded-lg shadow-2xl w-96 p-5 animate-modal-in"
        onClick={(e) => e.stopPropagation()}
        role="alertdialog"
        aria-modal="true"
      >
        <h3 className="font-display font-semibold text-base text-ink-900 dark:text-slate-100 mb-1.5">{title}</h3>
        <p className="text-sm text-ink-400 mb-5">{message}</p>
        <div className="flex gap-2">
          <button onClick={() => handle(false)} className="flex-1 bg-paper-dim dark:bg-slate-700 rounded-md py-2 text-sm font-medium">
            Abbrechen
          </button>
          <button
            ref={confirmBtnRef}
            onClick={() => handle(true)}
            className={`flex-1 rounded-md py-2 text-sm font-medium text-white ${danger ? "bg-conduit-600 hover:bg-conduit-700" : "bg-ink-900 hover:bg-blueprint"}`}
          >
            Bestätigen
          </button>
        </div>
      </div>
    </div>
  );
}

import { useToastStore } from "../store/useToastStore";

const ICON: Record<string, string> = { success: "✓", error: "!", info: "i" };
const STYLE: Record<string, string> = {
  success: "bg-signal-600 text-white",
  error: "bg-conduit-600 text-white",
  info: "bg-ink-900 text-white",
};

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          onClick={() => dismiss(t.id)}
          className={`${STYLE[t.type]} rounded-lg shadow-panel px-4 py-3 text-sm flex items-start gap-2.5 cursor-pointer animate-toast-in`}
        >
          <span className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
            {ICON[t.type]}
          </span>
          <span className="leading-snug">{t.message}</span>
        </div>
      ))}
    </div>
  );
}

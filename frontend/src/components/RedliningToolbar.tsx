export type RedliningTool = "none" | "trasse" | "schacht" | "kasten" | "muffe" | "verteiler" | "fcp";

const POINT_TOOLS: { tool: RedliningTool; label: string }[] = [
  { tool: "schacht", label: "Schacht" },
  { tool: "kasten", label: "Kasten" },
  { tool: "muffe", label: "Muffe" },
  { tool: "verteiler", label: "Verteiler" },
  { tool: "fcp", label: "FCP" },
];

interface Props {
  activeTool: RedliningTool;
  onSelectTool: (tool: RedliningTool) => void;
  drawingPointCount: number;
  drawingLengthM: number;
  onFinishLine: () => void;
  onUndoPoint: () => void;
  onCancel: () => void;
  canEdit: boolean;
}

export default function RedliningToolbar({
  activeTool, onSelectTool, drawingPointCount, drawingLengthM, onFinishLine, onUndoPoint, onCancel, canEdit,
}: Props) {
  if (!canEdit) return null;

  return (
    <div className="absolute top-3 left-3 right-3 sm:right-auto z-10 bg-white/95 dark:bg-slate-800/95 backdrop-blur rounded-lg shadow-panel border border-ink-100 dark:border-slate-700 p-2 flex items-center gap-1.5 text-xs overflow-x-auto max-w-full sm:max-w-none">
      <span className="text-ink-400 font-medium uppercase tracking-wide px-1.5 hidden sm:inline">Redlining</span>

      <button
        onClick={() => onSelectTool(activeTool === "trasse" ? "none" : "trasse")}
        className={`px-2.5 py-1.5 rounded-md font-medium transition ${
          activeTool === "trasse" ? "bg-conduit-500 text-white" : "bg-paper-dim dark:bg-slate-700 text-ink-600 dark:text-slate-200 hover:bg-ink-100"
        }`}
      >
        Trasse zeichnen
      </button>

      <div className="w-px h-5 bg-ink-100 dark:bg-slate-600 mx-0.5" />

      {POINT_TOOLS.map((pt) => (
        <button
          key={pt.tool}
          onClick={() => onSelectTool(activeTool === pt.tool ? "none" : pt.tool)}
          className={`px-2.5 py-1.5 rounded-md font-medium transition ${
            activeTool === pt.tool ? "bg-conduit-500 text-white" : "bg-paper-dim dark:bg-slate-700 text-ink-600 dark:text-slate-200 hover:bg-ink-100"
          }`}
        >
          {pt.label}
        </button>
      ))}

      {activeTool === "trasse" && (
        <>
          <div className="w-px h-5 bg-ink-100 dark:bg-slate-600 mx-0.5" />
          <span className="text-ink-400 font-data px-1">{drawingPointCount} Pkt · {drawingLengthM.toFixed(0)} m</span>
          <button onClick={onUndoPoint} disabled={drawingPointCount === 0} className="px-2 py-1.5 rounded-md bg-paper-dim dark:bg-slate-700 disabled:opacity-40">
            Zurück
          </button>
          <button onClick={onFinishLine} disabled={drawingPointCount < 2} className="px-2.5 py-1.5 rounded-md bg-ink-900 text-white disabled:opacity-40">
            Fertig
          </button>
        </>
      )}

      {activeTool !== "none" && (
        <button onClick={onCancel} className="px-2 py-1.5 rounded-md text-ink-400 hover:text-conduit-600">
          Abbrechen
        </button>
      )}
    </div>
  );
}

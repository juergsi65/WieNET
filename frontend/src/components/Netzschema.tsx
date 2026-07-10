import { useEffect, useMemo, useState } from "react";
import ReactFlow, { Background, Controls, Node, Edge, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { netzschemaApi } from "../lib/api";

interface NetzNode {
  id: string;
  name: string;
  typ: string;
  status: string;
  ports_gesamt: number | null;
  ports_belegt: number | null;
  belegung_pct: number | null;
  children: NetzNode[];
}

const TYP_FARBE: Record<string, string> = {
  olt: "#7c3aed", pon: "#a855f7", splitter: "#f59e0b", fcp: "#0ea5e9",
  muffe: "#eab308", hausanschluss: "#16a34a",
};

function layoutTree(roots: NetzNode[]) {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  let yCursor = 0;
  const X_GAP = 220;

  function visit(n: NetzNode, depth: number, parentId: string | null) {
    const myY = yCursor;
    if (n.children.length === 0) {
      yCursor += 90;
    } else {
      const startY = yCursor;
      n.children.forEach((c) => visit(c, depth + 1, n.id));
      const endY = yCursor;
      // Knoten vertikal mittig zu seinen Kindern positionieren, per nachträglichem Update
      const idx = nodes.findIndex((x) => x.id === n.id);
      if (idx >= 0) nodes[idx].position.y = (startY + endY - 90) / 2;
    }
    nodes.push({
      id: n.id,
      position: { x: depth * X_GAP, y: myY },
      data: {
        label: (
          <div>
            <div style={{ fontWeight: 600, fontSize: 12 }}>{n.name}</div>
            <div style={{ fontSize: 10, opacity: 0.7 }}>
              {n.ports_gesamt ? `${n.ports_belegt}/${n.ports_gesamt} Ports` : n.typ}
            </div>
          </div>
        ),
      },
      style: {
        border: `2px solid ${TYP_FARBE[n.typ] ?? "#64748b"}`,
        borderRadius: 8,
        padding: 6,
        background: n.status === "gestoert" ? "#fee2e2" : "#ffffff",
        width: 170,
      },
    });
    if (parentId) {
      edges.push({
        id: `${parentId}-${n.id}`,
        source: parentId,
        target: n.id,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: n.status === "gestoert" ? "#dc2626" : "#94a3b8" },
      });
    }
  }

  roots.forEach((r) => visit(r, 0, null));
  return { nodes, edges };
}

export default function Netzschema({ onSelectNode }: { onSelectNode?: (id: string, typ: string) => void }) {
  const [tree, setTree] = useState<NetzNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    netzschemaApi.baum().then((res) => setTree(res.data)).finally(() => setLoading(false));
  }, []);

  const { nodes, edges } = useMemo(() => layoutTree(tree), [tree]);

  if (loading) return <div className="p-4 text-sm text-slate-500">Netzschema wird geladen…</div>;
  if (tree.length === 0) return <div className="p-4 text-sm text-slate-500">Kein Netzschema hinterlegt.</div>;

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={(_, node) => {
          const flat = (list: NetzNode[]): NetzNode[] => list.flatMap((n) => [n, ...flat(n.children)]);
          const found = flat(tree).find((n) => n.id === node.id);
          if (found) onSelectNode?.(found.id, found.typ);
        }}
        fitView
        minZoom={0.2}
      >
        <Background gap={16} color="#e2e8f0" />
        <Controls />
      </ReactFlow>
    </div>
  );
}

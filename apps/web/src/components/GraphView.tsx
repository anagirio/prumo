import type { GraphData, Status } from "../types";

interface Props {
  graph: GraphData;
  status: Record<string, Status>;
  rootGaps?: string[];
  onSelect?: (conceptId: string) => void;
}

const NODE_W = 176;
const NODE_H = 40;
const GAP_X = 44;
const GAP_Y = 12;
const PAD = 12;

const FILL: Record<Status | "none", string> = {
  dominado: "#d8f3dc",
  lacuna: "#ffd6d6",
  incerto: "#fff1c2",
  none: "#eceff3",
};
const STROKE: Record<Status | "none", string> = {
  dominado: "#2d8a4e",
  lacuna: "#c0392b",
  incerto: "#b8860b",
  none: "#9aa5b1",
};

function shorten(text: string, max = 26): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

/** Layout em camadas: coluna = profundidade no grafo (pré-requisitos à esquerda). */
export default function GraphView({ graph, status, rootGaps = [], onSelect }: Props) {
  const columns = new Map<number, string[]>();
  for (const c of graph.concepts) {
    const d = graph.depth[c.id] ?? 0;
    columns.set(d, [...(columns.get(d) ?? []), c.id]);
  }
  const maxDepth = Math.max(...columns.keys());
  const maxRows = Math.max(...[...columns.values()].map((v) => v.length));

  const pos = new Map<string, { x: number; y: number }>();
  for (const [depth, ids] of columns) {
    ids.forEach((id, row) => {
      pos.set(id, {
        x: PAD + depth * (NODE_W + GAP_X),
        y: PAD + row * (NODE_H + GAP_Y),
      });
    });
  }

  const width = PAD * 2 + (maxDepth + 1) * NODE_W + maxDepth * GAP_X;
  const height = PAD * 2 + maxRows * NODE_H + (maxRows - 1) * GAP_Y;
  const roots = new Set(rootGaps);

  return (
    <div className="graph-scroll">
      <svg width={width} height={height} role="img" aria-label="Grafo de pré-requisitos">
        {graph.edges.map((e) => {
          const a = pos.get(e.from);
          const b = pos.get(e.to);
          if (!a || !b) return null;
          const x1 = a.x + NODE_W;
          const y1 = a.y + NODE_H / 2;
          const x2 = b.x;
          const y2 = b.y + NODE_H / 2;
          const mid = (x1 + x2) / 2;
          return (
            <path
              key={`${e.from}-${e.to}`}
              d={`M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`}
              fill="none"
              stroke="#c5ccd3"
              strokeWidth={1.2}
            />
          );
        })}
        {graph.concepts.map((c) => {
          const p = pos.get(c.id);
          if (!p) return null;
          const s: Status | "none" = (status[c.id] as Status | undefined) ?? "none";
          const isRoot = roots.has(c.id);
          return (
            <g
              key={c.id}
              transform={`translate(${p.x}, ${p.y})`}
              onClick={() => onSelect?.(c.id)}
              style={{ cursor: onSelect ? "pointer" : "default" }}
            >
              <title>{`${c.name} (${s === "none" ? "sem dados" : s})`}</title>
              <rect
                width={NODE_W}
                height={NODE_H}
                rx={8}
                fill={FILL[s]}
                stroke={STROKE[s]}
                strokeWidth={isRoot ? 3.5 : 1.5}
              />
              <text x={10} y={NODE_H / 2 + 4} fontSize={12} fill="#1f2933">
                {shorten(c.name)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

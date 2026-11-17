import { useMemo } from "react";
import type { GraphData, Status } from "../types";

type Variant = "full" | "mini";

interface Props {
  graph: GraphData;
  status?: Record<string, Status>;
  rootGaps?: string[];
  selected?: string | null;
  onSelect?: (conceptId: string) => void;
  variant?: Variant;
  /** Sem status ainda: manchas de lápis de cor por tema, como num croqui. */
  tintByTopic?: boolean;
}

const PITCH_X = 176;
const PITCH_Y = 96;
const PAD_X = 84;
const PAD_Y = 64;

const INK = "#1f2540";
const PENCILS = ["#6f8fd6", "#e59a52", "#7fb88f", "#c98ac0", "#e0c050"];

function hash(text: string): number {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10000) / 10000;
}

function shorten(text: string, max = 26): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

interface Layout {
  pos: Map<string, { x: number; y: number }>;
  width: number;
  height: number;
}

/** Colunas = profundidade no grafo; dentro da coluna, ordena pela média dos pré-requisitos. */
function computeLayout(graph: GraphData): Layout {
  const columns = new Map<number, string[]>();
  for (const c of graph.concepts) {
    const d = graph.depth[c.id] ?? 0;
    columns.set(d, [...(columns.get(d) ?? []), c.id]);
  }
  const depths = [...columns.keys()].sort((a, b) => a - b);
  const prereqs = new Map(graph.concepts.map((c) => [c.id, c.prerequisites]));
  const rowOf = new Map<string, number>();

  for (const d of depths) {
    const ids = columns.get(d) ?? [];
    const score = (id: string): number => {
      const ps = (prereqs.get(id) ?? []).map((p) => rowOf.get(p)).filter((v): v is number => v !== undefined);
      return ps.length ? ps.reduce((a, b) => a + b, 0) / ps.length : hash(id) * 10;
    };
    ids.sort((a, b) => score(a) - score(b) || a.localeCompare(b));
    ids.forEach((id, i) => rowOf.set(id, i));
  }

  const maxRows = Math.max(...[...columns.values()].map((v) => v.length));
  const pos = new Map<string, { x: number; y: number }>();
  for (const d of depths) {
    const ids = columns.get(d) ?? [];
    const offset = ((maxRows - ids.length) / 2) * PITCH_Y;
    ids.forEach((id, i) => {
      pos.set(id, {
        x: PAD_X + d * PITCH_X + (hash(`x${id}`) - 0.5) * 22,
        y: PAD_Y + offset + i * PITCH_Y + (hash(`y${id}`) - 0.5) * 22,
      });
    });
  }
  const maxDepth = Math.max(...depths);
  return {
    pos,
    width: PAD_X * 2 + maxDepth * PITCH_X,
    height: PAD_Y * 2 + (maxRows - 1) * PITCH_Y + 24,
  };
}

/** Elipse levemente torta, como um círculo feito à mão com caneta. */
function scribble(r: number, seed: string): string {
  const j = (k: string) => (hash(seed + k) - 0.5) * r * 0.22;
  const rx = r + j("a");
  const ry = r * 0.92 + j("b");
  const tilt = j("c");
  return [
    `M ${-rx} ${tilt}`,
    `C ${-rx} ${-ry * 1.15}, ${rx * 0.9} ${-ry * 1.2}, ${rx + j("d")} ${j("e")}`,
    `C ${rx} ${ry * 1.2}, ${-rx * 0.8} ${ry * 1.15}, ${-rx * 1.06} ${-ry * 0.25}`,
  ].join(" ");
}

export default function GraphView({
  graph,
  status = {},
  rootGaps = [],
  selected = null,
  onSelect,
  variant = "full",
  tintByTopic = false,
}: Props) {
  const { pos, width, height } = useMemo(() => computeLayout(graph), [graph]);
  const roots = new Set(rootGaps);
  const mini = variant === "mini";
  const fid = `rough-${variant}`;

  return (
    <svg
      className={`graph graph-${variant}`}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Mapa de pré-requisitos"
    >
      <defs>
        <filter id={fid} x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="4" result="n" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale={mini ? 2 : 3} />
        </filter>
        <marker id={`arrow-${variant}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M 1 1 L 9 5 L 1 9" fill="none" stroke={INK} strokeWidth="1.4" strokeLinecap="round" />
        </marker>
      </defs>

      {tintByTopic && (
        <g filter={`url(#${fid})`} opacity={0.5}>
          {graph.concepts.map((c) => {
            const p = pos.get(c.id);
            if (!p) return null;
            const color = PENCILS[Math.floor(hash(c.topics[0] ?? c.id) * PENCILS.length)];
            return <circle key={c.id} cx={p.x} cy={p.y} r={17} fill={color} />;
          })}
        </g>
      )}

      <g filter={`url(#${fid})`}>
        {graph.edges.map((e) => {
          const a = pos.get(e.from);
          const b = pos.get(e.to);
          if (!a || !b) return null;
          const mid = (a.x + b.x) / 2;
          const active = selected === e.from || selected === e.to;
          const dx = b.x - a.x;
          // para a seta antes de encostar no ponto de destino
          const endX = b.x - Math.sign(dx || 1) * 9;
          return (
            <path
              key={`${e.from}-${e.to}`}
              d={`M ${a.x + 8} ${a.y} C ${mid} ${a.y}, ${mid} ${b.y}, ${endX} ${b.y}`}
              className={active ? "edge edge-active" : "edge"}
              markerEnd={mini ? undefined : `url(#arrow-${variant})`}
            />
          );
        })}
      </g>

      {graph.concepts.map((c) => {
        const p = pos.get(c.id);
        if (!p) return null;
        const s = status[c.id] as Status | undefined;
        const isRoot = roots.has(c.id);
        const isSel = selected === c.id;
        const text = shorten(c.name);
        const hlWidth = text.length * 6.6 + 10;
        return (
          <g
            key={c.id}
            transform={`translate(${p.x}, ${p.y})`}
            className={onSelect ? "node clickable" : "node"}
            onClick={() => onSelect?.(c.id)}
            onKeyDown={(ev) => {
              if (onSelect && (ev.key === "Enter" || ev.key === " ")) {
                ev.preventDefault();
                onSelect(c.id);
              }
            }}
            tabIndex={onSelect ? 0 : undefined}
            role={onSelect ? "button" : undefined}
            aria-label={onSelect ? `${c.name}: ${s ?? "sem dados"}` : undefined}
          >
            <title>{`${c.name} (${s ?? "sem dados"})`}</title>
            <circle r={20} fill="transparent" />

            {!mini && s === "incerto" && (
              <rect x={-hlWidth / 2} y={13} width={hlWidth} height={17} rx={2} className="highlighter" />
            )}

            <g filter={`url(#${fid})`}>
              {s === "lacuna" && <path d={scribble(mini ? 9 : 13, c.id)} className="pen-red" />}
              {isRoot && <path d={scribble(mini ? 13 : 20, `${c.id}r`)} className="pen-red pen-thick" />}
              {isSel && <path d={scribble(mini ? 11 : 17, `${c.id}s`)} className="pen-ink" />}
              {s !== "dominado" && <circle r={mini ? 3.4 : 5.5} className={s === "lacuna" ? "dot dot-red" : "dot"} />}
              {s === "dominado" && (
                <path d="M -6 0.5 L -2 5 L 7 -6.5" className="check" transform={mini ? "scale(0.55)" : undefined} />
              )}
            </g>

            {!mini && (
              <text y={26} textAnchor="middle" className={isRoot || isSel ? "label label-strong" : "label"}>
                {text}
              </text>
            )}
            {!mini && isRoot && (
              <g className="note-root" transform="translate(-34, -38)">
                <text className="margin-note">comece aqui</text>
                <path d="M 30 6 C 40 8, 44 14, 42 24" className="note-arrow" fill="none" markerEnd={`url(#arrow-${variant})`} />
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
}

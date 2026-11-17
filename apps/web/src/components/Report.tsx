import { useState } from "react";
import type { DiagnosisReport, GraphData } from "../types";
import GraphView from "./GraphView";

interface Props {
  report: DiagnosisReport;
  graph: GraphData;
  onPlan: () => void;
}

export default function Report({ report, graph, onPlan }: Props) {
  const [selected, setSelected] = useState<string | null>(null);
  const name = (id: string) => graph.concepts.find((c) => c.id === id)?.name ?? id;
  const concept = graph.concepts.find((c) => c.id === selected);

  return (
    <div className="stack">
      <p className="lede">
        Com {report.questions_answered} perguntas, classificamos {report.mastered.length + report.gaps.length} de{" "}
        {report.total_concepts} conceitos. {report.uncertain.length} ainda ficaram na dúvida.
      </p>

      <div className="legend">
        <span className="key"><svg width="18" height="18" viewBox="-9 -9 18 18" aria-hidden="true"><path d="M -5 0.5 L -1.5 4.5 L 6 -5.5" className="check" /></svg> dominado {report.mastered.length}</span>
        <span className="key"><svg width="22" height="22" viewBox="-12 -12 24 24" aria-hidden="true"><ellipse rx="9" ry="8" className="pen-red" fill="none" /><circle r="3" className="dot dot-red" /></svg> lacuna {report.gaps.length}</span>
        <span className="key"><span className="hl-swatch" /> na dúvida {report.uncertain.length}</span>
        <span className="key"><span className="margin-note">clique num ponto para ver detalhes</span></span>
      </div>

      <div className="graph-panel">
        <GraphView
          graph={graph}
          status={report.status}
          rootGaps={report.root_gaps}
          selected={selected}
          onSelect={(id) => setSelected((cur) => (cur === id ? null : id))}
        />
      </div>

      {concept && (
        <div className="card detail">
          <p className="eyebrow">
            {report.status[concept.id] ?? "sem dados"} · domínio estimado{" "}
            {Math.round((report.mastery[concept.id] ?? 0.5) * 100)}%
          </p>
          <h3>{concept.name}</h3>
          <p>{concept.description}</p>
          {concept.prerequisites.length > 0 && (
            <p className="muted">Antes disso: {concept.prerequisites.map(name).join(", ")}</p>
          )}
        </div>
      )}

      <div className="two-col">
        <div className="card">
          <h3 className="card-title">Comece por aqui</h3>
          {report.root_gaps.length === 0 ? (
            <p>Nenhuma lacuna de base detectada.</p>
          ) : (
            <ol className="plain">
              {report.root_gaps.map((id) => (
                <li key={id}>{name(id)}</li>
              ))}
            </ol>
          )}
        </div>

        {report.misconceptions.length > 0 && (
          <div className="card">
            <h3 className="card-title">Onde o raciocínio escorregou</h3>
            <ul className="plain">
              {report.misconceptions.map((m) => (
                <li key={`${m.concept_id}-${m.text}`}>
                  <strong>{m.concept_name}.</strong> {m.text}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div>
        <button className="primary" onClick={onPlan}>
          Montar meu plano de estudo
        </button>
      </div>
    </div>
  );
}

import type { DiagnosisReport, GraphData } from "../types";
import GraphView from "./GraphView";

interface Props {
  report: DiagnosisReport;
  graph: GraphData;
  onPlan: () => void;
}

export default function Report({ report, graph, onPlan }: Props) {
  const name = (id: string) => graph.concepts.find((c) => c.id === id)?.name ?? id;

  return (
    <section className="card">
      <h2>Seu mapa de compreensão</h2>
      <p className="muted">
        Com {report.questions_answered} perguntas, classificamos {report.mastered.length + report.gaps.length} de{" "}
        {report.total_concepts} conceitos; {report.uncertain.length} continuam incertos.
      </p>

      <div className="legend">
        <span className="chip dominado">Dominado: {report.mastered.length}</span>
        <span className="chip lacuna">Lacuna: {report.gaps.length}</span>
        <span className="chip incerto">Incerto: {report.uncertain.length}</span>
      </div>

      <GraphView graph={graph} status={report.status} rootGaps={report.root_gaps} />
      <p className="muted small">Borda grossa: base mais funda que falta. É por aqui que o plano começa.</p>

      <h3>O que ensinar primeiro</h3>
      {report.root_gaps.length === 0 ? (
        <p>Nenhuma lacuna de base detectada.</p>
      ) : (
        <ol>
          {report.root_gaps.map((id) => (
            <li key={id}>{name(id)}</li>
          ))}
        </ol>
      )}

      {report.misconceptions.length > 0 && (
        <>
          <h3>Erros de raciocínio detectados</h3>
          <ul>
            {report.misconceptions.map((m) => (
              <li key={`${m.concept_id}-${m.text}`}>
                <strong>{m.concept_name}:</strong> {m.text}
              </li>
            ))}
          </ul>
        </>
      )}

      <button className="primary" onClick={onPlan}>
        Gerar meu plano de estudo
      </button>
    </section>
  );
}

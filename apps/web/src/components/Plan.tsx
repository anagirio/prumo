import { useState } from "react";
import { api } from "../api";
import type { Lesson, Plan as PlanData } from "../types";

interface Props {
  learnerId: string;
  plan: PlanData;
}

export default function Plan({ learnerId, plan }: Props) {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [error, setError] = useState<string | null>(null);

  const openLesson = async (conceptId: string) => {
    try {
      setLesson(await api.lesson(learnerId, conceptId));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const weeks = Array.from({ length: plan.weeks }, (_, i) => i + 1);

  return (
    <section className="card">
      <h2>Seu plano</h2>
      <p className="muted">
        {plan.steps.length} passos · cerca de {Math.round(plan.total_minutes / 60)} h no total ·{" "}
        {plan.weeks} semanas · {plan.skipped_mastered} conceitos já dominados foram pulados.
      </p>
      {error && <p className="error">{error}</p>}
      {plan.steps.length === 0 && <p>Você já domina tudo o que mapeamos. Parabéns!</p>}
      {weeks.map((w) => (
        <div key={w} className="week">
          <h3>Semana {w}</h3>
          <ol>
            {plan.steps
              .filter((s) => s.week === w)
              .map((s) => (
                <li key={s.concept_id} value={s.order}>
                  <div className="step">
                    <div>
                      <strong>{s.name}</strong>{" "}
                      <span className={`chip ${s.kind === "fundamento" ? "lacuna" : "incerto"}`}>
                        {s.kind === "fundamento" ? "fundamento" : "conteúdo"}
                      </span>
                      <div className="muted small">
                        {s.reason} · {s.est_minutes} min
                      </div>
                    </div>
                    <button onClick={() => void openLesson(s.concept_id)}>Abrir aula</button>
                  </div>
                </li>
              ))}
          </ol>
        </div>
      ))}

      {lesson && (
        <div className="lesson">
          <h3>{lesson.title}</h3>
          <p className="muted small">
            {lesson.source === "llm" ? "Aula gerada por IA" : "Aula padrão (modo sem IA)"}
          </p>
          <ol>
            {lesson.steps.map((s, i) => (
              <li key={i}>
                <span className="chip incerto">{s.kind}</span> {s.text}
              </li>
            ))}
          </ol>
          <button onClick={() => setLesson(null)}>Fechar</button>
        </div>
      )}
    </section>
  );
}

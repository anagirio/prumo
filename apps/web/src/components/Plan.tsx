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
    <div className="stack">
      <p className="lede">
        {plan.steps.length} passos, cerca de {Math.round(plan.total_minutes / 60)} h em {plan.weeks} semanas.{" "}
        {plan.skipped_mastered}{" "}
        {plan.skipped_mastered === 1 ? "conceito que você já domina foi pulado" : "conceitos que você já domina foram pulados"}.
      </p>
      {error && <p className="error">{error}</p>}
      {plan.steps.length === 0 && <p>Você já domina tudo o que mapeamos. Parabéns!</p>}

      {weeks.map((w) => (
        <section key={w} className="week">
          <h3 className="week-title">Semana {w}</h3>
          <ul className="steps-list">
            {plan.steps
              .filter((s) => s.week === w)
              .map((s) => (
                <li key={s.concept_id} className="plan-row">
                  <span className="box" aria-hidden="true" />
                  <div className="grow">
                    <div className="row-title">
                      {s.name}{" "}
                      <span className={s.kind === "fundamento" ? "tag tag-red" : "tag"}>
                        {s.kind === "fundamento" ? "fundamento" : "conteúdo"}
                      </span>
                    </div>
                    <div className="muted small">{s.reason}</div>
                  </div>
                  <span className="minutes">{s.est_minutes} min</span>
                  <button onClick={() => void openLesson(s.concept_id)}>Abrir aula</button>
                </li>
              ))}
          </ul>
        </section>
      ))}

      {lesson && (
        <section className="sticky-note lesson" aria-label={`Aula: ${lesson.title}`}>
          <div className="lesson-head">
            <h3>{lesson.title}</h3>
            <span className="margin-note">
              {lesson.source === "llm" ? "aula gerada por IA" : "aula padrão (sem IA)"}
            </span>
          </div>
          <ol className="plain lesson-steps">
            {lesson.steps.map((s, i) => (
              <li key={i}>
                <p className="pen small-pen">{s.kind}</p>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
          <button onClick={() => setLesson(null)}>Fechar</button>
        </section>
      )}
    </div>
  );
}

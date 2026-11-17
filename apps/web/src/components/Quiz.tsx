import { useEffect, useState } from "react";
import { api } from "../api";
import type { AnswerOut, PublicQuestion, StateOut } from "../types";

interface Props {
  learnerId: string;
  onState: (state: StateOut) => void;
  onDone: () => void;
}

export default function Quiz({ learnerId, onState, onDone }: Props) {
  const [question, setQuestion] = useState<PublicQuestion | null>(null);
  const [progress, setProgress] = useState({ answered: 0, max: 12 });
  const [feedback, setFeedback] = useState<AnswerOut | null>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadNext = async () => {
    try {
      const next = await api.next(learnerId);
      setProgress({ answered: next.answered, max: next.max_questions });
      if (next.done || !next.question) {
        onDone();
        return;
      }
      setQuestion(next.question);
      setFeedback(null);
      setPicked(null);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    void loadNext();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const choose = async (optionId: string) => {
    if (!question || feedback) return;
    setPicked(optionId);
    try {
      const out = await api.answer(learnerId, question.id, optionId);
      setFeedback(out);
      onState(out.state);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  if (error) return <p className="error">{error}</p>;
  if (!question) return <p>Carregando pergunta…</p>;

  return (
    <section className="card">
      <p className="muted">
        Pergunta {progress.answered + (feedback ? 0 : 1)} (no máximo {progress.max}) ·{" "}
        {question.concept_name}
      </p>
      <h2 className="prompt">{question.prompt}</h2>
      <ul className="options">
        {question.options.map((o) => {
          let cls = "option";
          if (feedback) {
            if (o.id === feedback.correct_option_id) cls += " correct";
            else if (o.id === picked) cls += " wrong";
          }
          return (
            <li key={o.id}>
              <button className={cls} disabled={!!feedback} onClick={() => void choose(o.id)}>
                <strong>{o.id.toUpperCase()})</strong> {o.text}
              </button>
            </li>
          );
        })}
      </ul>
      {feedback && (
        <div className={`feedback ${feedback.correct ? "ok" : "no"}`}>
          <p>
            <strong>{feedback.correct ? "Certo." : "Não foi dessa vez."}</strong>{" "}
            {feedback.explanation}
          </p>
          {feedback.misconception && (
            <p>
              <em>O que essa escolha sugere:</em> {feedback.misconception}
            </p>
          )}
          <button className="primary" onClick={() => void loadNext()}>
            Continuar
          </button>
        </div>
      )}
    </section>
  );
}

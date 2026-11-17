import { useEffect, useState } from "react";
import { api } from "../api";
import type { AnswerOut, PublicQuestion, StateOut } from "../types";

interface Props {
  learnerId: string;
  onState: (state: StateOut) => void;
  onProgress: (answered: number, max: number) => void;
  onDone: () => void;
}

export default function Quiz({ learnerId, onState, onProgress, onDone }: Props) {
  const [question, setQuestion] = useState<PublicQuestion | null>(null);
  const [progress, setProgress] = useState({ answered: 0, max: 12 });
  const [feedback, setFeedback] = useState<AnswerOut | null>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadNext = async () => {
    try {
      const next = await api.next(learnerId);
      setProgress({ answered: next.answered, max: next.max_questions });
      onProgress(next.answered, next.max_questions);
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

  // Atalhos: letra escolhe a alternativa, Enter continua.
  useEffect(() => {
    const onKey = (ev: KeyboardEvent) => {
      if (ev.metaKey || ev.ctrlKey || ev.altKey) return;
      const target = ev.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA"].includes(target.tagName)) return;
      if (feedback && ev.key === "Enter") {
        ev.preventDefault();
        void loadNext();
      } else if (!feedback && question) {
        const id = ev.key.toLowerCase();
        if (question.options.some((o) => o.id === id)) void choose(id);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question, feedback]);

  if (error) return <p className="error">{error}</p>;
  if (!question) return <p className="muted">Carregando pergunta…</p>;

  const current = progress.answered + (feedback ? 0 : 1);

  return (
    <section className="prova" aria-live="polite">
      <div className="prova-body">
        <div className="prova-head">
          <span className="qnum">{current}</span>
          <span className="tema">tema: {question.concept_name}</span>
        </div>
        <div className="bubbles" aria-hidden="true">
          {Array.from({ length: progress.max }, (_, i) => (
            <span key={i} className={i < progress.answered + (feedback ? 1 : 0) ? "bub on" : "bub"} />
          ))}
        </div>
        <h2 className="prompt">{question.prompt}</h2>

        <ul className="options">
          {question.options.map((o) => {
            let cls = "option";
            let mark = o.id.toUpperCase();
            if (feedback) {
              if (o.id === feedback.correct_option_id) {
                cls += " correct";
                mark = "✓";
              } else if (o.id === picked) {
                cls += " wrong";
                mark = "✗";
              }
            } else if (o.id === picked) cls += " picked";
            return (
              <li key={o.id}>
                <button className={cls} disabled={!!feedback} onClick={() => void choose(o.id)}>
                  <span className="bubble" aria-hidden="true">{mark}</span>
                  <span className="sr-only">Alternativa {o.id.toUpperCase()}: </span>
                  <span>{o.text}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      {feedback ? (
        <div className={`correcao ${feedback.correct ? "ok" : "no"}`}>
          <p className="pen">{feedback.correct ? "Certo!" : "Não foi dessa vez."}</p>
          <p>{feedback.explanation}</p>
          {feedback.misconception && (
            <p className="margin-note-block">
              <span className="pen small-pen">o que essa escolha sugere:</span> {feedback.misconception}
            </p>
          )}
          <div className="actions">
            <span className="hint">Enter continua</span>
            <button className="primary" onClick={() => void loadNext()}>
              Continuar
            </button>
          </div>
        </div>
      ) : (
        <div className="correcao idle">
          <span className="hint">
            Teclas {question.options.map((o) => o.id.toUpperCase()).join(", ")} marcam a alternativa
          </span>
        </div>
      )}
    </section>
  );
}

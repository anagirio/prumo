import { useEffect, useState } from "react";
import { api } from "../api";
import type { PracticeCheck, PublicQuestion } from "../types";

interface Props {
  learnerId: string;
  conceptId: string;
}

const MAX_TRIES_BEFORE_REVEAL = 2;

// Exercício de fixação: errou, ganha uma pista (o raciocínio por trás da alternativa
// escolhida), não o gabarito. Só depois de duas tentativas o aluno pode ver a resposta.
export default function Practice({ learnerId, conceptId }: Props) {
  const [question, setQuestion] = useState<PublicQuestion | null>(null);
  const [seen, setSeen] = useState<string[]>([]);
  const [wrong, setWrong] = useState<string[]>([]);
  const [hint, setHint] = useState<string | null>(null);
  const [result, setResult] = useState<PracticeCheck | null>(null);
  const [finished, setFinished] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (exclude: string[]) => {
    try {
      const { question: q } = await api.practice(learnerId, conceptId, exclude);
      setWrong([]);
      setHint(null);
      setResult(null);
      if (!q) {
        setFinished(true);
        return;
      }
      setQuestion(q);
      setSeen([...exclude, q.id]);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    void load([]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conceptId]);

  const choose = async (optionId: string) => {
    if (!question || result?.correct_option_id) return;
    try {
      const out = await api.practiceCheck(question.id, optionId);
      if (out.correct) {
        setResult(out);
        setHint(null);
      } else {
        setWrong((w) => [...w, optionId]);
        setHint(out.hint);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const reveal = async () => {
    if (!question) return;
    try {
      setResult(await api.practiceCheck(question.id, wrong[wrong.length - 1], true));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  if (error) return <p className="error">{error}</p>;
  if (finished)
    return <p className="pen">Acabaram os exercícios deste tema. Volte ao plano e siga em frente!</p>;
  if (!question) return <p className="muted">Carregando exercício…</p>;

  const done = !!result?.correct_option_id;

  return (
    <div className="practice" aria-live="polite">
      <p className="pen small-pen">exercício, sem pressa</p>
      <h4 className="prompt">{question.prompt}</h4>
      <ul className="options">
        {question.options.map((o) => {
          let cls = "option";
          let mark = o.id.toUpperCase();
          if (done && o.id === result?.correct_option_id) {
            cls += " correct";
            mark = "✓";
          } else if (wrong.includes(o.id)) {
            cls += " wrong";
            mark = "✗";
          }
          return (
            <li key={o.id}>
              <button
                className={cls}
                disabled={done || wrong.includes(o.id)}
                onClick={() => void choose(o.id)}
              >
                <span className="bubble" aria-hidden="true">{mark}</span>
                <span>{o.text}</span>
              </button>
            </li>
          );
        })}
      </ul>

      {!done && hint && (
        <div className="correcao no">
          <p className="pen">Quase. Uma pista:</p>
          <p>{hint}</p>
          <p className="hint">Tente de novo com outra alternativa.</p>
        </div>
      )}

      {!done && wrong.length >= MAX_TRIES_BEFORE_REVEAL && (
        <button onClick={() => void reveal()}>Mostrar a resposta</button>
      )}

      {done && (
        <div className={`correcao ${result?.correct ? "ok" : "no"}`}>
          <p className="pen">{result?.correct ? "Isso!" : "Aqui vai a resposta:"}</p>
          <p>{result?.explanation}</p>
          <div className="actions">
            <button className="primary" onClick={() => void load(seen)}>
              Outro exercício
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

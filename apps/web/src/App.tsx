import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import GraphView from "./components/GraphView";
import Plan from "./components/Plan";
import Quiz from "./components/Quiz";
import Report from "./components/Report";
import type { DiagnosisReport, GraphData, Plan as PlanData, StateOut } from "./types";

type Screen = "intro" | "quiz" | "report" | "plan";

export default function App() {
  const [screen, setScreen] = useState<Screen>("intro");
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [learnerId, setLearnerId] = useState<string | null>(null);
  const [liveState, setLiveState] = useState<StateOut | null>(null);
  const [report, setReport] = useState<DiagnosisReport | null>(null);
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.graph().then(setGraph).catch((e: Error) => setError(e.message));
  }, []);

  const start = async () => {
    try {
      const { learner_id } = await api.createLearner();
      setLearnerId(learner_id);
      setLiveState(null);
      setReport(null);
      setPlan(null);
      setScreen("quiz");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const finishQuiz = useCallback(async () => {
    if (!learnerId) return;
    try {
      setReport(await api.report(learnerId));
      setScreen("report");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [learnerId]);

  const makePlan = async () => {
    if (!learnerId) return;
    try {
      setPlan(await api.plan(learnerId));
      setScreen("plan");
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <main className="app">
      <header>
        <h1>Prumo</h1>
        <p className="tagline">
          Descubra o que falta antes de estudar o que cai. Tutor de Língua Portuguesa para concursos.
        </p>
      </header>

      {error && (
        <p className="error">
          {error}. O backend está rodando em http://localhost:8000?
        </p>
      )}

      {screen === "intro" && (
        <section className="card">
          <h2>Como funciona</h2>
          <ol>
            <li>Você responde poucas perguntas, escolhidas uma a uma pelo que mais revela sobre você.</li>
            <li>Mapeamos o que você entende (e o que falta) num grafo de pré-requisitos.</li>
            <li>Seu plano começa pela base que falta, não pelo peso da matéria.</li>
          </ol>
          <button className="primary" onClick={() => void start()} disabled={!graph}>
            Começar o diagnóstico
          </button>
        </section>
      )}

      {screen === "quiz" && learnerId && (
        <>
          <Quiz learnerId={learnerId} onState={setLiveState} onDone={() => void finishQuiz()} />
          {graph && liveState && (
            <section className="card">
              <h3>Seu mapa, ao vivo</h3>
              <GraphView graph={graph} status={liveState.status} />
            </section>
          )}
        </>
      )}

      {screen === "report" && report && graph && (
        <Report report={report} graph={graph} onPlan={() => void makePlan()} />
      )}

      {screen === "plan" && plan && learnerId && <Plan learnerId={learnerId} plan={plan} />}

      {(screen === "report" || screen === "plan") && (
        <button onClick={() => void start()}>Refazer o diagnóstico</button>
      )}
    </main>
  );
}

import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import GraphView from "./components/GraphView";
import Plan from "./components/Plan";
import Quiz from "./components/Quiz";
import Report from "./components/Report";
import type { DiagnosisReport, GraphData, Plan as PlanData, StateOut } from "./types";

type Screen = "intro" | "quiz" | "report" | "plan";

const TITLES: Record<Exclude<Screen, "intro">, string> = {
  quiz: "Diagnóstico",
  report: "Seu mapa",
  plan: "Seu plano",
};

export default function App() {
  const [screen, setScreen] = useState<Screen>("intro");
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [learnerId, setLearnerId] = useState<string | null>(null);
  const [liveState, setLiveState] = useState<StateOut | null>(null);
  const [progress, setProgress] = useState({ answered: 0, max: 12 });
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
      setProgress({ answered: 0, max: 12 });
      setError(null);
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

  const tabs: { id: Screen; label: string; enabled: boolean }[] = [
    { id: "quiz", label: "Diagnóstico", enabled: !!learnerId && !report },
    { id: "report", label: "Mapa", enabled: !!report },
    { id: "plan", label: "Plano", enabled: !!plan },
  ];

  // Quanto o fio de prumo já desceu pela margem.
  const p =
    screen === "intro" ? 0 : screen === "quiz" ? 0.1 + 0.6 * (progress.answered / progress.max) : screen === "report" ? 0.8 : 0.95;
  const bobNote =
    screen === "intro"
      ? "começa aqui"
      : screen === "quiz"
        ? `${progress.answered} de ${progress.max}`
        : screen === "report"
          ? "base à vista"
          : "mãos à obra";

  return (
    <div className="page" style={{ ["--p" as string]: p }}>
      <div className="margin-line" aria-hidden="true" />
      <div className="plumb" aria-hidden="true">
        <svg width="26" height="64" viewBox="0 0 26 64">
          <circle cx="13" cy="4" r="3" className="nail" />
          <line x1="13" y1="7" x2="13" y2="38" className="thread" />
          <path d="M 13 56 L 6 40 Q 13 36 20 40 Z" className="bob" />
          <circle cx="13" cy="58" r="1.6" className="nail" />
        </svg>
        <span className="margin-note">{bobNote}</span>
      </div>

      <header className="top">
        <button className="wordmark" onClick={() => setScreen("intro")} aria-label="Voltar ao início">
          prumo
        </button>
        <nav className="tabs" aria-label="Etapas">
          {tabs.map((t, i) => (
            <button
              key={t.id}
              className={screen === t.id ? "tab active" : "tab"}
              disabled={!t.enabled}
              onClick={() => setScreen(t.id)}
            >
              <span className="tab-n">{i + 1}</span> {t.label}
            </button>
          ))}
        </nav>
      </header>

      {error && (
        <p className="error">
          {error}. O backend está rodando em http://localhost:8000?
        </p>
      )}

      <main className="sheet">
        {screen === "intro" ? (
          <section className="hero">
            <h1 className="hero-title">
              Descubra <mark className="hl">o que falta</mark> antes de estudar <s className="strike">o que cai</s>.
            </h1>
            <p className="lede">
              Poucas perguntas, escolhidas uma a uma pelo que mais revelam. O mapa mostra qual base está faltando, e
              o plano de estudo começa por ela, não pelo peso da matéria.
            </p>
            <div className="cta-row">
              <button className="primary big" onClick={() => void start()} disabled={!graph}>
                Começar o diagnóstico
              </button>
              <span className="margin-note">Língua Portuguesa · até 12 perguntas · sem cadastro</span>
            </div>
            <div className="graph-panel hero-graph">{graph && <GraphView graph={graph} tintByTopic />}</div>
          </section>
        ) : (
          <>
            <h1 className="page-title">{TITLES[screen]}</h1>

            {screen === "quiz" && learnerId && (
              <div className="quiz-layout">
                <Quiz
                  learnerId={learnerId}
                  onState={setLiveState}
                  onProgress={(answered, max) => setProgress({ answered, max })}
                  onDone={() => void finishQuiz()}
                />
                {graph && liveState && (
                  <aside className="minimap" aria-label="Seu mapa ao vivo">
                    <span className="tape" aria-hidden="true" />
                    <p className="margin-note">rascunho do seu mapa</p>
                    <GraphView graph={graph} status={liveState.status} variant="mini" />
                  </aside>
                )}
              </div>
            )}

            {screen === "report" && report && graph && (
              <Report report={report} graph={graph} onPlan={() => void makePlan()} />
            )}

            {screen === "plan" && plan && learnerId && <Plan learnerId={learnerId} plan={plan} />}

            {(screen === "report" || screen === "plan") && (
              <div className="footer-actions">
                <button onClick={() => void start()}>Refazer o diagnóstico</button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

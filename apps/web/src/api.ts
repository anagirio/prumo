import type {
  AnswerOut,
  DiagnosisReport,
  GraphData,
  Lesson,
  NextQuestionOut,
  Plan,
  StateOut,
} from "./types";

const BASE: string = import.meta.env.VITE_API_BASE ?? "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`Erro ${res.status} em ${path}`);
  }
  return (await res.json()) as T;
}

export const api = {
  graph: () => req<GraphData>("/graph"),
  createLearner: () => req<{ learner_id: string }>("/learners", { method: "POST" }),
  state: (id: string) => req<StateOut>(`/learners/${id}/state`),
  next: (id: string) => req<NextQuestionOut>(`/learners/${id}/diagnosis/next`, { method: "POST" }),
  answer: (id: string, questionId: string, optionId: string) =>
    req<AnswerOut>(`/learners/${id}/diagnosis/answer`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, option_id: optionId }),
    }),
  report: (id: string) => req<DiagnosisReport>(`/learners/${id}/report`),
  plan: (id: string, minutesPerWeek = 300) =>
    req<Plan>(`/learners/${id}/plan?minutes_per_week=${minutesPerWeek}`),
  lesson: (id: string, conceptId: string) =>
    req<Lesson>(`/learners/${id}/lessons`, {
      method: "POST",
      body: JSON.stringify({ concept_id: conceptId }),
    }),
};

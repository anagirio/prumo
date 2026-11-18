export type Status = "dominado" | "lacuna" | "incerto";

export interface Concept {
  id: string;
  name: string;
  description: string;
  prerequisites: string[];
  topics: string[];
  weight: number;
}

export interface GraphData {
  concepts: Concept[];
  edges: { from: string; to: string }[];
  depth: Record<string, number>;
}

export interface PublicQuestion {
  id: string;
  concept_id: string;
  concept_name: string;
  prompt: string;
  options: { id: string; text: string }[];
}

export interface StateOut {
  answered: number;
  mastery: Record<string, number>;
  status: Record<string, Status>;
}

export interface NextQuestionOut {
  done: boolean;
  question: PublicQuestion | null;
  answered: number;
  max_questions: number;
}

export interface AnswerOut {
  correct: boolean;
  correct_option_id: string;
  explanation: string;
  misconception: string | null;
  suspects: string[];
  state: StateOut;
}

export interface MisconceptionFinding {
  concept_id: string;
  concept_name: string;
  text: string;
  count: number;
}

export interface DiagnosisReport {
  questions_answered: number;
  total_concepts: number;
  mastered: string[];
  gaps: string[];
  uncertain: string[];
  root_gaps: string[];
  misconceptions: MisconceptionFinding[];
  mastery: Record<string, number>;
  status: Record<string, Status>;
}

export interface PlanStep {
  order: number;
  week: number;
  concept_id: string;
  name: string;
  kind: "fundamento" | "conteudo";
  reason: string;
  blocked_by: string[];
  est_minutes: number;
  mastery: number;
}

export interface Plan {
  steps: PlanStep[];
  total_minutes: number;
  weeks: number;
  skipped_mastered: number;
}

export interface LessonStep {
  kind: "prever" | "explicar" | "revisar" | "atencao" | "exercicio" | "dica" | "verificar";
  text: string;
}

export interface Lesson {
  concept_id: string;
  title: string;
  steps: LessonStep[];
  source: "mock" | "llm";
}

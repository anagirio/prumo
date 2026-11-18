"""Modelos de dados compartilhados (conteúdo, estado do aluno, respostas da API)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["dominado", "lacuna", "incerto"]


# ---------------------------------------------------------------- conteúdo


class Concept(BaseModel):
    """Um nó do grafo: algo que o aluno precisa entender."""

    id: str
    name: str
    description: str
    prerequisites: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)  # tópicos de edital que este conceito atende
    weight: float = 1.0  # importância estimada em provas (calibrar com provas anteriores)


class Option(BaseModel):
    id: str
    text: str
    # O que essa alternativa errada revela sobre o aluno (None na correta).
    misconception: str | None = None
    # Pré-requisitos que provavelmente faltam quando o aluno escolhe esta alternativa.
    suspect_prerequisites: list[str] = Field(default_factory=list)


class Question(BaseModel):
    id: str
    concept_id: str
    prompt: str
    options: list[Option]
    correct_option_id: str
    explanation: str

    def option(self, option_id: str) -> Option:
        for opt in self.options:
            if opt.id == option_id:
                return opt
        raise KeyError(option_id)


class PublicOption(BaseModel):
    id: str
    text: str


class PublicQuestion(BaseModel):
    """Versão da questão enviada ao aluno: sem gabarito nem diagnóstico."""

    id: str
    concept_id: str
    concept_name: str
    prompt: str
    options: list[PublicOption]

    @classmethod
    def from_question(cls, q: Question, concept_name: str) -> PublicQuestion:
        return cls(
            id=q.id,
            concept_id=q.concept_id,
            concept_name=concept_name,
            prompt=q.prompt,
            options=[PublicOption(id=o.id, text=o.text) for o in q.options],
        )


# ---------------------------------------------------------------- aluno


class AnswerRecord(BaseModel):
    question_id: str
    concept_id: str
    option_id: str
    correct: bool


class MisconceptionFinding(BaseModel):
    concept_id: str
    concept_name: str
    text: str
    count: int


class DiagnosisReport(BaseModel):
    questions_answered: int
    total_concepts: int
    mastered: list[str]
    gaps: list[str]
    uncertain: list[str]
    # Lacunas cujos pré-requisitos não são lacunas: o que ensinar primeiro.
    root_gaps: list[str]
    misconceptions: list[MisconceptionFinding]
    mastery: dict[str, float]
    status: dict[str, Status]


# ---------------------------------------------------------------- plano


class PlanStep(BaseModel):
    order: int
    week: int
    concept_id: str
    name: str
    kind: Literal["fundamento", "conteudo"]
    reason: str
    blocked_by: list[str]
    est_minutes: int
    mastery: float


class Plan(BaseModel):
    steps: list[PlanStep]
    total_minutes: int
    weeks: int
    skipped_mastered: int


# ---------------------------------------------------------------- aula


class LessonStep(BaseModel):
    kind: Literal["prever", "explicar", "revisar", "atencao", "exercicio", "dica", "verificar"]
    text: str


class Lesson(BaseModel):
    concept_id: str
    title: str
    steps: list[LessonStep]
    source: Literal["mock", "llm"] = "mock"

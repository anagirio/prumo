"""Carrega e valida o conteúdo (grafo e banco de questões) a partir de YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from prumo.graph import KnowledgeGraph
from prumo.models import Concept, Question

CONTENT_DIR = Path(__file__).parent / "content"
DEFAULT_GRAPH = CONTENT_DIR / "portugues.yaml"
DEFAULT_QUESTIONS = CONTENT_DIR / "questoes_portugues.yaml"


class ContentError(ValueError):
    """Conteúdo inconsistente (questão sem conceito, gabarito inexistente, etc.)."""


class QuestionBank:
    def __init__(self, graph: KnowledgeGraph, questions: list[Question]):
        self.graph = graph
        self._by_id: dict[str, Question] = {}
        self._by_concept: dict[str, list[Question]] = {cid: [] for cid in graph.concepts}
        for q in questions:
            self._validate(q)
            self._by_id[q.id] = q
            self._by_concept[q.concept_id].append(q)

    def _validate(self, q: Question) -> None:
        if q.id in self._by_id:
            raise ContentError(f"questão duplicada: {q.id}")
        if q.concept_id not in self.graph.concepts:
            raise ContentError(f"{q.id}: conceito inexistente {q.concept_id}")
        ids = [o.id for o in q.options]
        if len(ids) < 3 or len(set(ids)) != len(ids):
            raise ContentError(f"{q.id}: precisa de 3+ alternativas com ids únicos")
        if q.correct_option_id not in ids:
            raise ContentError(f"{q.id}: gabarito {q.correct_option_id} não existe")
        ancestors = self.graph.ancestors(q.concept_id)
        for o in q.options:
            if o.id == q.correct_option_id:
                if o.misconception or o.suspect_prerequisites:
                    raise ContentError(f"{q.id}: a alternativa correta não deve ter diagnóstico")
                continue
            if not o.misconception:
                raise ContentError(f"{q.id}/{o.id}: distrator sem concepção errada descrita")
            for s in o.suspect_prerequisites:
                if s not in ancestors:
                    raise ContentError(
                        f"{q.id}/{o.id}: suspeito {s} não é pré-requisito de {q.concept_id}"
                    )

    def get(self, question_id: str) -> Question:
        try:
            return self._by_id[question_id]
        except KeyError:
            raise KeyError(question_id) from None

    def for_concept(self, concept_id: str) -> list[Question]:
        return list(self._by_concept[concept_id])

    def all(self) -> list[Question]:
        return list(self._by_id.values())


def load_graph(path: Path | None = None) -> KnowledgeGraph:
    data = yaml.safe_load((path or DEFAULT_GRAPH).read_text(encoding="utf-8"))
    return KnowledgeGraph(Concept(**c) for c in data["concepts"])


def load_question_bank(graph: KnowledgeGraph, path: Path | None = None) -> QuestionBank:
    data = yaml.safe_load((path or DEFAULT_QUESTIONS).read_text(encoding="utf-8"))
    return QuestionBank(graph, [Question(**q) for q in data["questions"]])

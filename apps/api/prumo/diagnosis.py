"""Diagnóstico adaptativo: escolhe a próxima pergunta que mais informa sobre o aluno.

Ideia: perguntar sobre conceitos incertos que, quando resolvidos, esclarecem muitos outros
(porque têm muitos pré-requisitos e dependentes). Para quando tudo está classificado
ou o orçamento de perguntas acaba.
"""

from __future__ import annotations

from collections import Counter

from prumo.content import QuestionBank
from prumo.graph import KnowledgeGraph
from prumo.learner import LearnerModel, status_of
from prumo.models import DiagnosisReport, MisconceptionFinding, Question

# Pesos da seleção de perguntas, calibrados em sementes de treino e medidos em sementes de
# teste separadas (scripts/calibrate.py, docs/EVALUATION.md).
REACH_WEIGHT = 0.0
GAP_DESCENT_BONUS = 1.0
SUSPECT_BONUS = 2.0


class DiagnosisEngine:
    def __init__(self, graph: KnowledgeGraph, bank: QuestionBank, max_questions: int = 12):
        self.graph = graph
        self.bank = bank
        self.max_questions = max_questions

    # ------------------------------------------------------------ seleção

    def _candidates(self, model: LearnerModel) -> list[tuple[str, Question]]:
        asked = model.asked_question_ids()
        out: list[tuple[str, Question]] = []
        for cid in self.graph.topological_order():
            if model.status(cid) != "incerto":
                continue
            fresh = [q for q in self.bank.for_concept(cid) if q.id not in asked]
            if fresh:
                out.append((cid, fresh[0]))
        return out

    def _suspected(self, model: LearnerModel) -> set[str]:
        """Pré-requisitos apontados como suspeitos por alternativas erradas já escolhidas."""
        out: set[str] = set()
        for h in model.history:
            if not h.correct:
                out.update(self.bank.get(h.question_id).option(h.option_id).suspect_prerequisites)
        return out

    def score(self, model: LearnerModel, cid: str, suspected: set[str] | None = None) -> float:
        """Valor de perguntar sobre cid.

        incerteza x (leve) alcance no grafo x peso no edital x bônus de "descida":
        quando um conceito falha, sondar primeiro os pré-requisitos incertos dele (e os
        apontados como suspeitos) para achar a base mais funda que falta.
        """
        suspected = self._suspected(model) if suspected is None else suspected
        p = model.mastery[cid]
        uncertainty = 4 * p * (1 - p)  # 1.0 em p=0.5
        reach = len(self.graph.ancestors(cid)) + len(self.graph.descendants(cid))
        failing_dependents = sum(
            1 for d in self.graph.dependents(cid) if model.status(d) == "lacuna"
        )
        weight = self.graph.concepts[cid].weight
        return (
            uncertainty
            * (1 + REACH_WEIGHT * reach)
            * (1 + GAP_DESCENT_BONUS * failing_dependents)
            * (1 + SUSPECT_BONUS * (cid in suspected))
            * (0.8 + 0.2 * weight)
        )

    def next_question(self, model: LearnerModel) -> Question | None:
        if len(model.history) >= self.max_questions:
            return None
        candidates = self._candidates(model)
        if not candidates:
            return None
        suspected = self._suspected(model)
        # max() devolve o primeiro empate: desempate estável pela ordem topológica.
        _, question = max(candidates, key=lambda cq: self.score(model, cq[0], suspected))
        return question

    def is_done(self, model: LearnerModel) -> bool:
        return self.next_question(model) is None

    # ------------------------------------------------------------ relatório

    def report(self, model: LearnerModel) -> DiagnosisReport:
        status = {cid: status_of(p) for cid, p in model.mastery.items()}
        order = self.graph.topological_order()
        mastered = [c for c in order if status[c] == "dominado"]
        gaps = [c for c in order if status[c] == "lacuna"]
        uncertain = [c for c in order if status[c] == "incerto"]

        gap_set = set(gaps)
        root = [c for c in gaps if not any(p in gap_set for p in self.graph.prerequisites(c))]
        root.sort(key=lambda c: (-len(self.graph.descendants(c)), self.graph.topo_index(c)))

        counter: Counter[tuple[str, str]] = Counter()
        for h in model.history:
            if h.correct:
                continue
            opt = self.bank.get(h.question_id).option(h.option_id)
            if opt.misconception:
                counter[(h.concept_id, opt.misconception)] += 1
        findings = [
            MisconceptionFinding(
                concept_id=cid,
                concept_name=self.graph.concepts[cid].name,
                text=text,
                count=n,
            )
            for (cid, text), n in counter.most_common()
        ]

        return DiagnosisReport(
            questions_answered=len(model.history),
            total_concepts=len(order),
            mastered=mastered,
            gaps=gaps,
            uncertain=uncertain,
            root_gaps=root,
            misconceptions=findings,
            mastery={c: round(model.mastery[c], 3) for c in order},
            status=status,
        )

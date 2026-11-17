"""Modelo de crença do aluno: quanto ele provavelmente domina cada conceito.

Cada resposta atualiza a crença no conceito da questão (Bayes com chute e deslize) e
propaga evidência pelo grafo:

* acerto  -> pré-requisitos ficam mais prováveis de serem dominados;
* erro    -> a culpa é dividida: alternativas erradas apontam pré-requisitos suspeitos
             (que perdem mais crença) e os dependentes do conceito ficam menos prováveis.

Os números abaixo são heurísticas explícitas e ajustáveis, não valores aprendidos.
"""

from __future__ import annotations

from dataclasses import dataclass

from prumo.graph import KnowledgeGraph
from prumo.models import AnswerRecord, Question, Status

PRIOR = 0.5
MASTERED_AT = 0.7  # p >= isso: dominado
GAP_AT = 0.35  # p <= isso: lacuna
SLIP = 0.10  # prob. de errar sabendo
MIN_P, MAX_P = 0.02, 0.98

ACERTO_BOOST = 0.6  # força do reforço nos pré-requisitos após um acerto
SUSPECT_FACTOR = 0.5  # fator aplicado a pré-requisitos suspeitos após um erro
DIRECT_PREREQ_FACTOR = 0.85  # fator aplicado aos demais pré-requisitos diretos após um erro
DEPENDENT_PENALTY = 0.25  # penalidade máxima nos dependentes após um erro
INFERRED_BLAME_FLOOR = GAP_AT + 0.01  # culpa inferida não classifica pré-requisito como lacuna


def clamp(p: float) -> float:
    return min(MAX_P, max(MIN_P, p))


def status_of(p: float) -> Status:
    if p >= MASTERED_AT:
        return "dominado"
    if p <= GAP_AT:
        return "lacuna"
    return "incerto"


@dataclass
class AnswerFeedback:
    correct: bool
    posterior: float
    misconception: str | None
    suspects: list[str]


class LearnerModel:
    def __init__(
        self,
        graph: KnowledgeGraph,
        mastery: dict[str, float] | None = None,
        history: list[AnswerRecord] | None = None,
        propagate: bool = True,
    ):
        self.graph = graph
        self.mastery: dict[str, float] = {cid: PRIOR for cid in graph.concepts}
        if mastery:
            self.mastery.update({k: v for k, v in mastery.items() if k in graph.concepts})
        self.history: list[AnswerRecord] = list(history or [])
        self.propagate = propagate

    # ------------------------------------------------------------ consulta

    def asked_question_ids(self) -> set[str]:
        return {h.question_id for h in self.history}

    def status(self, cid: str) -> Status:
        return status_of(self.mastery[cid])

    def statuses(self) -> dict[str, Status]:
        return {cid: status_of(p) for cid, p in self.mastery.items()}

    # ------------------------------------------------------------ atualização

    def observe(self, question: Question, option_id: str) -> AnswerFeedback:
        option = question.option(option_id)
        correct = option_id == question.correct_option_id
        cid = question.concept_id

        guess = min(0.35, max(0.10, 1.0 / len(question.options)))
        p = self.mastery[cid]
        if correct:
            post = p * (1 - SLIP) / (p * (1 - SLIP) + (1 - p) * guess)
        else:
            post = p * SLIP / (p * SLIP + (1 - p) * (1 - guess))
        self.mastery[cid] = clamp(post)

        suspects: list[str] = []
        if self.propagate:
            if correct:
                self._reinforce_ancestors(cid, post)
            else:
                suspects = self._blame(cid, post, option.suspect_prerequisites)

        self.history.append(
            AnswerRecord(
                question_id=question.id, concept_id=cid, option_id=option_id, correct=correct
            )
        )
        return AnswerFeedback(
            correct=correct,
            posterior=self.mastery[cid],
            misconception=None if correct else option.misconception,
            suspects=suspects,
        )

    def _reinforce_ancestors(self, cid: str, post: float) -> None:
        for anc, dist in self.graph.ancestors(cid).items():
            boost = post * ACERTO_BOOST * (0.5**dist)
            p = self.mastery[anc]
            self.mastery[anc] = clamp(p + (1 - p) * boost)

    def _blame(self, cid: str, post: float, suspect_ids: list[str]) -> list[str]:
        suspects = [s for s in suspect_ids if s in self.graph.concepts]
        observed = {h.concept_id for h in self.history}

        def blamed(c: str, factor: float) -> float:
            # Culpa por inferência nunca vira "lacuna" sozinha: o pré-requisito precisa ser
            # testado. Só evidência direta (uma resposta sobre ele) pode derrubá-lo até lacuna.
            floor = MIN_P if c in observed else INFERRED_BLAME_FLOOR
            return min(self.mastery[c], max(floor, self.mastery[c] * factor))

        for s in suspects:
            self.mastery[s] = blamed(s, SUSPECT_FACTOR)
        for p in self.graph.prerequisites(cid):
            if p not in suspects:
                self.mastery[p] = blamed(p, DIRECT_PREREQ_FACTOR)
        for desc, dist in self.graph.descendants(cid).items():
            factor = 1 - DEPENDENT_PENALTY * (0.5 ** (dist - 1)) * (1 - post)
            self.mastery[desc] = clamp(self.mastery[desc] * factor)
        return suspects

    # ------------------------------------------------------------ persistência

    def to_dict(self) -> dict:
        return {
            "mastery": self.mastery,
            "history": [h.model_dump() for h in self.history],
        }

    @classmethod
    def from_dict(cls, graph: KnowledgeGraph, data: dict) -> LearnerModel:
        return cls(
            graph,
            mastery=data.get("mastery"),
            history=[AnswerRecord(**h) for h in data.get("history", [])],
        )

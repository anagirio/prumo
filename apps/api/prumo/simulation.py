"""Simulação de alunos sintéticos para avaliar a mecânica do diagnóstico.

ATENÇÃO: o aluno sintético é gerado com a mesma hipótese estrutural que o motor assume
(lacuna num conceito derruba os dependentes). Isso valida a MECÂNICA (o diagnóstico
adaptativo aproveita melhor um orçamento curto de perguntas), não prova eficácia com
pessoas reais. A validação real é o piloto com concurseiros (ver docs/EVALUATION.md).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from prumo.content import QuestionBank
from prumo.diagnosis import DiagnosisEngine
from prumo.graph import KnowledgeGraph
from prumo.learner import LearnerModel
from prumo.models import Question

STRATEGIES = ("adaptive", "random_propagate", "random_flat")


@dataclass
class SyntheticStudent:
    known: set[str]
    true_root_gaps: set[str]
    rng: random.Random
    slip: float = 0.10

    def answer(self, q: Question) -> str:
        wrong = [o.id for o in q.options if o.id != q.correct_option_id]
        if q.concept_id in self.known:
            if self.rng.random() > self.slip:
                return q.correct_option_id
            return self.rng.choice(wrong)
        if self.rng.random() < 1.0 / len(q.options):  # chute
            return q.correct_option_id
        return self.rng.choice(wrong)


@dataclass(frozen=True)
class Population:
    """Como os alunos sintéticos são gerados. Variar isso testa a robustez do motor."""

    name: str = "padrao"
    max_root_gaps: int = 3
    noise: float = 0.05
    slip: float = 0.10


POPULATIONS = (
    Population("padrao"),
    Population("ruidosa", noise=0.15),
    Population("desatenta", slip=0.20),
    Population("muitas_lacunas", max_root_gaps=5),
    Population("poucas_lacunas", max_root_gaps=1, noise=0.02),
)


def make_student(
    graph: KnowledgeGraph,
    rng: random.Random,
    max_root_gaps: int = 3,
    noise: float = 0.05,
    max_unknown_fraction: float = 0.7,
    slip: float = 0.10,
) -> SyntheticStudent:
    ids = list(graph.concepts)
    for _ in range(50):
        roots = set(rng.sample(ids, rng.randint(1, max_root_gaps)))
        unknown = set(roots)
        for r in roots:
            unknown.update(graph.descendants(r))
        if len(unknown) <= max_unknown_fraction * len(ids):
            break
    for cid in ids:  # ruído: lacunas e acertos isolados que não seguem a estrutura
        if rng.random() < noise:
            unknown.symmetric_difference_update({cid})
    known = set(ids) - unknown
    true_roots = {c for c in unknown if not any(p in unknown for p in graph.prerequisites(c))}
    return SyntheticStudent(known=known, true_root_gaps=true_roots, rng=rng, slip=slip)


def run_session(
    graph: KnowledgeGraph,
    bank: QuestionBank,
    student: SyntheticStudent,
    strategy: str,
    max_questions: int,
    rng: random.Random,
) -> LearnerModel:
    model = LearnerModel(graph, propagate=(strategy != "random_flat"))
    engine = DiagnosisEngine(graph, bank, max_questions=max_questions)
    all_questions = bank.all()
    for _ in range(max_questions):
        if strategy == "adaptive":
            q = engine.next_question(model)
        else:
            asked = model.asked_question_ids()
            pool = [x for x in all_questions if x.id not in asked]
            q = rng.choice(pool) if pool else None
        if q is None:
            break
        model.observe(q, student.answer(q))
    return model


@dataclass
class Metrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    root_recall: float
    root_precision: float
    avg_questions: float
    brier: float = 0.0  # erro quadrático de P(não domina) vs. verdade (menor = melhor)
    ece: float = 0.0  # erro de calibração esperado em 10 faixas (menor = melhor)

    @property
    def root_f1(self) -> float:
        p, r = self.root_precision, self.root_recall
        return 2 * p * r / (p + r) if p + r else 0.0

    @property
    def objective(self) -> float:
        """Critério único usado na calibração: média de F1 de lacunas e F1 de bases."""
        return (self.f1 + self.root_f1) / 2


def evaluate(
    graph: KnowledgeGraph,
    bank: QuestionBank,
    n_students: int = 300,
    max_questions: int = 12,
    seed: int = 7,
    strategies: tuple[str, ...] = STRATEGIES,
    population: Population | None = None,
) -> dict[str, Metrics]:
    engine = DiagnosisEngine(graph, bank, max_questions=max_questions)
    pop = population or Population()
    results: dict[str, Metrics] = {}
    ids = list(graph.concepts)
    for strategy in strategies:
        rng = random.Random(seed)  # mesma sequência de alunos para todas as estratégias
        acc = prec = rec = f1 = root_rec = root_prec = qs = brier = 0.0
        bins = [[0, 0.0, 0.0] for _ in range(10)]  # n, soma das probabilidades, soma dos y
        for _ in range(n_students):
            student = make_student(graph, rng, pop.max_root_gaps, pop.noise, slip=pop.slip)
            model = run_session(graph, bank, student, strategy, max_questions, rng)
            unknown_true = set(ids) - student.known
            unknown_pred = {c for c in ids if model.mastery[c] < 0.5}
            tp = len(unknown_true & unknown_pred)
            fp = len(unknown_pred - unknown_true)
            fn = len(unknown_true - unknown_pred)
            tn = len(ids) - tp - fp - fn
            p = tp / (tp + fp) if tp + fp else 0.0
            r = tp / (tp + fn) if tp + fn else 1.0
            acc += (tp + tn) / len(ids)
            prec += p
            rec += r
            f1 += 2 * p * r / (p + r) if p + r else 0.0
            predicted_roots = set(engine.report(model).root_gaps)
            hits = len(student.true_root_gaps & predicted_roots)
            root_rec += hits / len(student.true_root_gaps) if student.true_root_gaps else 1.0
            root_prec += hits / len(predicted_roots) if predicted_roots else 0.0
            qs += len(model.history)
            for c in ids:
                p_unknown = 1.0 - model.mastery[c]
                y = 1.0 if c in unknown_true else 0.0
                brier += (p_unknown - y) ** 2 / len(ids)
                b = bins[min(9, int(p_unknown * 10))]
                b[0] += 1
                b[1] += p_unknown
                b[2] += y
        n = float(n_students)
        total = sum(b[0] for b in bins)
        ece = sum(abs(b[1] - b[2]) for b in bins if b[0]) / total if total else 0.0
        results[strategy] = Metrics(
            acc / n, prec / n, rec / n, f1 / n, root_rec / n, root_prec / n, qs / n, brier / n, ece
        )
    return results

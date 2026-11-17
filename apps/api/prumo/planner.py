"""Plano de estudo: ordem de aprendizagem respeitando pré-requisitos.

Diferente de um cronograma por peso de matéria: o que falta de base vem antes do que
depende dela, e conceitos que destravam muitos outros sobem na fila.
"""

from __future__ import annotations

from prumo.graph import KnowledgeGraph
from prumo.learner import GAP_AT, MASTERED_AT, LearnerModel
from prumo.models import Plan, PlanStep

BASE_MINUTES = 30


def estimate_minutes(mastery: float) -> int:
    """30 min se já está quase lá, até 60 min se é totalmente novo."""
    return round(BASE_MINUTES * (1 + (1 - mastery)))


def build_plan(
    graph: KnowledgeGraph,
    model: LearnerModel,
    targets: list[str] | None = None,
    minutes_per_week: int = 300,
) -> Plan:
    if minutes_per_week <= 0:
        raise ValueError("minutes_per_week deve ser positivo")
    target_set = set(targets) if targets else set(graph.concepts)
    unknown = target_set - set(graph.concepts)
    if unknown:
        raise KeyError(min(unknown))

    scope = graph.closure(target_set)
    pending = {c for c in scope if model.mastery[c] < MASTERED_AT}
    skipped = len(scope) - len(pending)

    def pending_dependents(c: str) -> list[str]:
        return [d for d in graph.descendants(c) if d in pending]

    def priority(c: str) -> float:
        return graph.concepts[c].weight * (1 + 0.2 * len(pending_dependents(c)))

    scheduled: list[str] = []
    done: set[str] = set()
    remaining = set(pending)
    while remaining:
        ready = [
            c
            for c in remaining
            if all(p not in pending or p in done for p in graph.prerequisites(c))
        ]
        ready.sort(key=lambda c: (-priority(c), graph.topo_index(c)))
        nxt = ready[0]
        scheduled.append(nxt)
        done.add(nxt)
        remaining.remove(nxt)

    steps: list[PlanStep] = []
    week, week_minutes, total = 1, 0, 0
    for i, cid in enumerate(scheduled, start=1):
        minutes = estimate_minutes(model.mastery[cid])
        if week_minutes + minutes > minutes_per_week and week_minutes > 0:
            week += 1
            week_minutes = 0
        week_minutes += minutes
        total += minutes

        deps = pending_dependents(cid)
        kind = "fundamento" if deps else "conteudo"
        if model.mastery[cid] <= GAP_AT:
            reason = "Lacuna detectada"
            if deps:
                names = ", ".join(
                    graph.concepts[d].name for d in sorted(deps, key=graph.topo_index)[:3]
                )
                reason += f" e base para: {names}"
        else:
            reason = "Ainda incerto: revisar e confirmar"
        steps.append(
            PlanStep(
                order=i,
                week=week,
                concept_id=cid,
                name=graph.concepts[cid].name,
                kind=kind,
                reason=reason,
                blocked_by=[p for p in graph.prerequisites(cid) if p in pending],
                est_minutes=minutes,
                mastery=round(model.mastery[cid], 3),
            )
        )

    return Plan(
        steps=steps, total_minutes=total, weeks=week if steps else 0, skipped_mastered=skipped
    )

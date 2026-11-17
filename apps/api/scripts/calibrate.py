"""Calibração honesta dos parâmetros do motor, com treino e teste separados.

Problema que isto corrige: ajustar parâmetros e reportar o resultado nos mesmos alunos
sintéticos superestima o ganho. Aqui:

* os parâmetros são escolhidos só com sementes de TREINO, num mix de 5 populações de alunos;
* o resultado final é medido em sementes de TESTE nunca vistas, com erro-padrão entre sementes;
* só se muda um parâmetro se o ganho no treino passar de MIN_GAIN (evita perseguir ruído);
* a robustez é checada em populações com premissas diferentes (mais ruído, mais deslizes...).

Uso: python scripts/calibrate.py [--apply-report docs-path]
"""

from __future__ import annotations

import argparse
import contextlib
import json
import statistics
import sys
from collections.abc import Iterator
from pathlib import Path

from prumo import diagnosis, learner
from prumo.content import load_graph, load_question_bank
from prumo.simulation import POPULATIONS, Metrics, Population, evaluate

TRAIN_SEEDS = list(range(100, 108))
TEST_SEEDS = list(range(500, 520))
N_TRAIN, N_TEST = 200, 300
MIN_GAIN = 0.002

# (módulo, nome, valores candidatos)
PARAMS: list[tuple[object, str, list[float]]] = [
    (learner, "SLIP", [0.05, 0.10, 0.15, 0.20]),
    (learner, "ACERTO_BOOST", [0.3, 0.6, 0.9]),
    (learner, "SUSPECT_FACTOR", [0.3, 0.5, 0.7]),
    (learner, "DIRECT_PREREQ_FACTOR", [0.7, 0.85, 1.0]),
    (learner, "DEPENDENT_PENALTY", [0.1, 0.25, 0.4]),
    (learner, "GAP_AT", [0.25, 0.35, 0.45]),
    (learner, "MASTERED_AT", [0.6, 0.7, 0.8]),
    (diagnosis, "REACH_WEIGHT", [0.0, 0.02, 0.05]),
    (diagnosis, "GAP_DESCENT_BONUS", [0.0, 1.0, 2.0, 4.0]),
    (diagnosis, "SUSPECT_BONUS", [0.0, 1.0, 2.0]),
]


@contextlib.contextmanager
def patched(values: dict[str, float]) -> Iterator[None]:
    """Aplica valores nas constantes dos módulos e restaura ao sair."""
    mods = {name: mod for mod, name, _ in PARAMS}
    saved = {name: getattr(mods[name], name) for name in values}
    saved_floor = learner.INFERRED_BLAME_FLOOR
    try:
        for name, v in values.items():
            setattr(mods[name], name, v)
        learner.INFERRED_BLAME_FLOOR = learner.GAP_AT + 0.01
        yield
    finally:
        for name, v in saved.items():
            setattr(mods[name], name, v)
        learner.INFERRED_BLAME_FLOOR = saved_floor


def current() -> dict[str, float]:
    return {name: getattr(mod, name) for mod, name, _ in PARAMS}


def run(
    values: dict[str, float], seeds: list[int], n: int, pop: Population, strategies: tuple[str, ...]
):
    graph = load_graph()
    bank = load_question_bank(graph)
    out: dict[str, list[Metrics]] = {s: [] for s in strategies}
    with patched(values):
        for seed in seeds:
            res = evaluate(graph, bank, n, 12, seed, strategies, pop)
            for s in strategies:
                out[s].append(res[s])
    return out


def mean_se(xs: list[float]) -> tuple[float, float]:
    m = statistics.fmean(xs)
    se = statistics.stdev(xs) / len(xs) ** 0.5 if len(xs) > 1 else 0.0
    return m, se


def train_objective(values: dict[str, float]) -> float:
    scores = []
    for pop in POPULATIONS:
        ms = run(values, TRAIN_SEEDS, N_TRAIN, pop, ("adaptive",))["adaptive"]
        scores.append(statistics.fmean(m.objective for m in ms))
    return statistics.fmean(scores)


def coordinate_descent(
    start: dict[str, float], rounds: int = 2
) -> tuple[dict[str, float], list[str]]:
    best = dict(start)
    best_score = train_objective(best)
    log = [f"início: objetivo de treino = {best_score:.4f}"]
    for r in range(rounds):
        changed = False
        for _, name, candidates in PARAMS:
            scored = {}
            for v in candidates:
                trial = {**best, name: v}
                scored[v] = best_score if v == best[name] else train_objective(trial)
            top_v = max(scored, key=lambda v: scored[v])
            if top_v != best[name] and scored[top_v] - best_score > MIN_GAIN:
                log.append(
                    f"rodada {r + 1}: {name} {best[name]} -> {top_v} "
                    f"({best_score:.4f} -> {scored[top_v]:.4f})"
                )
                best[name], best_score, changed = top_v, scored[top_v], True
            else:
                log.append(
                    f"rodada {r + 1}: {name} fica em {best[name]} "
                    f"(melhor alternativa {top_v}: {scored[top_v] - best_score:+.4f}, abaixo de {MIN_GAIN})"
                )
        if not changed:
            break
    log.append(f"fim: objetivo de treino = {best_score:.4f}")
    return best, log


def test_table(tag: str, values: dict[str, float]) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for pop in POPULATIONS:
        res = run(values, TEST_SEEDS, N_TEST, pop, ("adaptive", "random_propagate", "random_flat"))
        row = {}
        for s, ms in res.items():
            row[s] = {
                "objective": mean_se([m.objective for m in ms]),
                "f1": mean_se([m.f1 for m in ms]),
                "root_recall": mean_se([m.root_recall for m in ms]),
                "root_precision": mean_se([m.root_precision for m in ms]),
                "brier": mean_se([m.brier for m in ms]),
                "ece": mean_se([m.ece for m in ms]),
            }
        diffs = [
            a.objective - b.objective for a, b in zip(res["adaptive"], res["random_propagate"])
        ]
        row["adaptive_minus_random_propagate"] = mean_se(diffs)
        rows[pop.name] = row
    print(f"\n=== TESTE ({tag}) ===")
    for name, row in rows.items():
        a, rp, rf = row["adaptive"], row["random_propagate"], row["random_flat"]
        d, dse = row["adaptive_minus_random_propagate"]
        print(
            f"{name:15s} obj adaptativo {a['objective'][0]:.3f}±{a['objective'][1]:.3f} | "
            f"aleat+prop {rp['objective'][0]:.3f} | aleat {rf['objective'][0]:.3f} | "
            f"dif vs aleat+prop {d:+.3f}±{dse:.3f} | brier {a['brier'][0]:.3f} ece {a['ece'][0]:.3f}"
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--out", default="calibration_result.json")
    args = ap.parse_args()

    default = current()
    print("parâmetros atuais:", json.dumps(default))
    before = test_table("parâmetros atuais", default)
    tuned, log = coordinate_descent(default, args.rounds)
    print("\n".join(log))
    print("parâmetros calibrados:", json.dumps(tuned))
    after = test_table("parâmetros calibrados", tuned)
    Path(args.out).write_text(
        json.dumps(
            {"default": default, "tuned": tuned, "log": log, "before": before, "after": after},
            indent=2,
        )
    )
    print(f"\nresultado salvo em {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()

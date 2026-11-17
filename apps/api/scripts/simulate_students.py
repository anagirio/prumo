"""Compara o diagnóstico adaptativo com baselines usando alunos sintéticos.

Uso (a partir de apps/api):  python scripts/simulate_students.py --students 500 --max-questions 12
"""

from __future__ import annotations

import argparse

from prumo.content import load_graph, load_question_bank
from prumo.simulation import evaluate

LABELS = {
    "adaptive": "Adaptativo (grafo + próxima pergunta mais informativa)",
    "random_propagate": "Aleatório com propagação no grafo",
    "random_flat": "Aleatório sem grafo (cada conceito isolado)",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--students", type=int, default=300)
    ap.add_argument("--max-questions", type=int, default=12)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    graph = load_graph()
    bank = load_question_bank(graph)
    results = evaluate(graph, bank, args.students, args.max_questions, args.seed)

    print(
        f"{args.students} alunos sintéticos, até {args.max_questions} perguntas, seed {args.seed}\n"
    )
    print(
        "| Estratégia | Acurácia | Precisão | Revocação | F1 | Lacunas-raiz: revocação | "
        "Lacunas-raiz: precisão | Perguntas |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for key, m in results.items():
        print(
            f"| {LABELS[key]} | {m.accuracy:.3f} | {m.precision:.3f} | {m.recall:.3f} | "
            f"{m.f1:.3f} | {m.root_recall:.3f} | {m.root_precision:.3f} | {m.avg_questions:.1f} |"
        )


if __name__ == "__main__":
    main()

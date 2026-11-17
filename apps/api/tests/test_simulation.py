from prumo.content import load_graph, load_question_bank
from prumo.simulation import POPULATIONS, evaluate


def _mean_objective(strategy, graph, bank, population):
    seeds = (11, 12, 13)
    return sum(
        evaluate(graph, bank, 150, 12, s, (strategy,), population)[strategy].objective
        for s in seeds
    ) / len(seeds)


def test_adaptive_selection_beats_random_with_propagation_in_every_population():
    """Valida a mecânica, não a eficácia com pessoas reais (ver docs/EVALUATION.md).

    Roda nas 5 populações de alunos sintéticos, em sementes diferentes das usadas na calibração
    (treino 100-107, teste 500-519), para não premiar só o caso favorável.
    """
    graph = load_graph()
    bank = load_question_bank(graph)
    for pop in POPULATIONS:
        adaptive = _mean_objective("adaptive", graph, bank, pop)
        baseline = _mean_objective("random_propagate", graph, bank, pop)
        assert adaptive > baseline, f"{pop.name}: {adaptive:.3f} <= {baseline:.3f}"


def test_graph_propagation_beats_flat_questions():
    graph = load_graph()
    bank = load_question_bank(graph)
    res = evaluate(graph, bank, n_students=300, max_questions=12, seed=7)
    assert res["adaptive"].f1 > res["random_flat"].f1 + 0.05
    assert res["adaptive"].brier < res["random_flat"].brier

from prumo.content import load_graph, load_question_bank
from prumo.simulation import evaluate


def test_graph_and_adaptive_selection_beat_baselines_on_synthetic_students():
    """Valida a mecânica (não a eficácia com pessoas reais; ver docs/EVALUATION.md)."""
    graph = load_graph()
    bank = load_question_bank(graph)
    res = evaluate(graph, bank, n_students=300, max_questions=12, seed=7)
    # O grafo ajuda muito: sem propagação, o mesmo orçamento de perguntas rende bem menos.
    assert res["adaptive"].f1 > res["random_flat"].f1 + 0.05
    # A escolha adaptativa da próxima pergunta não é pior que sortear com propagação.
    assert res["adaptive"].f1 >= res["random_propagate"].f1
    assert res["adaptive"].root_precision >= res["random_propagate"].root_precision

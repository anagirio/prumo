import pytest

from prumo.content import ContentError, QuestionBank, load_graph, load_question_bank
from prumo.graph import GraphError, KnowledgeGraph
from prumo.models import Concept, Option, Question


def c(cid, prereqs=()):
    return Concept(id=cid, name=cid, description="d", prerequisites=list(prereqs))


def test_toposort_respects_prerequisites():
    g = KnowledgeGraph([c("c", ["b"]), c("b", ["a"]), c("a")])
    order = g.topological_order()
    assert order.index("a") < order.index("b") < order.index("c")


def test_ancestors_and_descendants_have_distances():
    g = KnowledgeGraph([c("a"), c("b", ["a"]), c("c", ["b"]), c("d", ["a", "c"])])
    assert g.ancestors("d") == {"a": 1, "c": 1, "b": 2}
    assert g.descendants("a") == {"b": 1, "d": 1, "c": 2}
    assert g.depth("d") == 3


def test_closure_includes_all_prerequisites():
    g = KnowledgeGraph([c("a"), c("b", ["a"]), c("c", ["b"]), c("x")])
    assert g.closure(["c"]) == {"a", "b", "c"}


def test_cycle_is_rejected():
    with pytest.raises(GraphError):
        KnowledgeGraph([c("a", ["b"]), c("b", ["a"])])


def test_unknown_prerequisite_is_rejected():
    with pytest.raises(GraphError):
        KnowledgeGraph([c("a", ["nope"])])


def test_seed_graph_loads_and_is_acyclic():
    g = load_graph()
    assert len(g.concepts) == 24
    assert g.depth("reescrita-frases") >= 5  # a cadeia de dependências é profunda de verdade


def test_every_seed_concept_has_a_question():
    g = load_graph()
    bank = load_question_bank(g)
    missing = [cid for cid in g.concepts if not bank.for_concept(cid)]
    assert missing == []


def test_every_wrong_option_names_a_misconception():
    bank = load_question_bank(load_graph())
    for q in bank.all():
        for o in q.options:
            if o.id != q.correct_option_id:
                assert o.misconception, f"{q.id}/{o.id}"


def test_bank_rejects_suspect_that_is_not_a_prerequisite():
    g = KnowledgeGraph([c("a"), c("b", ["a"]), c("x")])
    bad = Question(
        id="q",
        concept_id="b",
        prompt="?",
        options=[
            Option(id="1", text="ok"),
            Option(id="2", text="no", misconception="m", suspect_prerequisites=["x"]),
            Option(id="3", text="no", misconception="m"),
        ],
        correct_option_id="1",
        explanation="e",
    )
    with pytest.raises(ContentError):
        QuestionBank(g, [bad])


def test_bank_rejects_missing_correct_option():
    g = KnowledgeGraph([c("a")])
    bad = Question(
        id="q",
        concept_id="a",
        prompt="?",
        options=[Option(id="1", text="x", misconception="m")] * 1
        + [
            Option(id="2", text="y", misconception="m"),
            Option(id="3", text="z", misconception="m"),
        ],
        correct_option_id="9",
        explanation="e",
    )
    with pytest.raises(ContentError):
        QuestionBank(g, [bad])

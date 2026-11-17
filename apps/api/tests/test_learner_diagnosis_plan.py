from prumo.content import load_graph, load_question_bank
from prumo.diagnosis import DiagnosisEngine
from prumo.learner import MASTERED_AT, LearnerModel
from prumo.planner import build_plan

graph = load_graph()
bank = load_question_bank(graph)


def wrong_option(q):
    return next(o.id for o in q.options if o.id != q.correct_option_id)


def test_correct_answer_raises_concept_and_prerequisites():
    q = bank.for_concept("subordinacao-substantiva")[0]
    m = LearnerModel(graph)
    m.observe(q, q.correct_option_id)
    assert m.mastery["subordinacao-substantiva"] > 0.5
    for anc in graph.ancestors("subordinacao-substantiva"):
        assert m.mastery[anc] > 0.5


def test_wrong_answer_lowers_concept_and_dependents():
    q = bank.for_concept("coordenacao")[0]
    m = LearnerModel(graph)
    m.observe(q, wrong_option(q))
    assert m.mastery["coordenacao"] < 0.5
    for desc in graph.descendants("coordenacao"):
        assert m.mastery[desc] < 0.5


def test_wrong_answer_blames_the_suspect_prerequisite_most():
    q = bank.for_concept("reescrita-frases")[0]
    wrong = next(o for o in q.options if o.suspect_prerequisites)
    m = LearnerModel(graph)
    fb = m.observe(q, wrong.id)
    assert fb.misconception
    suspect = wrong.suspect_prerequisites[0]
    other = next(
        p for p in graph.ancestors("reescrita-frases") if p not in wrong.suspect_prerequisites
    )
    assert m.mastery[suspect] < m.mastery[other]


def test_model_roundtrips_through_dict():
    q = bank.for_concept("crase")[0]
    m = LearnerModel(graph)
    m.observe(q, q.correct_option_id)
    m2 = LearnerModel.from_dict(graph, m.to_dict())
    assert m2.mastery == m.mastery
    assert m2.asked_question_ids() == m.asked_question_ids()


def test_diagnosis_never_repeats_a_question_and_respects_budget():
    engine = DiagnosisEngine(graph, bank, max_questions=8)
    m = LearnerModel(graph)
    seen = set()
    while (q := engine.next_question(m)) is not None:
        assert q.id not in seen
        seen.add(q.id)
        m.observe(q, q.correct_option_id)
    assert len(seen) <= 8


def test_diagnosis_asks_fewer_questions_than_concepts_for_a_strong_student():
    engine = DiagnosisEngine(graph, bank, max_questions=24)
    m = LearnerModel(graph)
    n = 0
    while (q := engine.next_question(m)) is not None:
        m.observe(q, q.correct_option_id)
        n += 1
    assert n < len(graph.concepts)  # a propagação economiza perguntas


def test_report_finds_root_gap_not_its_dependents():
    engine = DiagnosisEngine(graph, bank, max_questions=24)
    m = LearnerModel(graph)
    # aluno que não entende subordinação substantiva (e portanto o que depende dela)
    broken = {"subordinacao-substantiva"} | set(graph.descendants("subordinacao-substantiva"))
    while (q := engine.next_question(m)) is not None:
        m.observe(q, wrong_option(q) if q.concept_id in broken else q.correct_option_id)
    report = engine.report(m)
    assert "subordinacao-substantiva" in report.gaps
    assert report.root_gaps[0] == "subordinacao-substantiva"
    assert "pontuacao" not in report.root_gaps  # depende dela, então não é raiz
    assert report.misconceptions


def test_plan_respects_prerequisite_order_and_skips_mastered():
    m = LearnerModel(graph)
    for cid in graph.concepts:
        m.mastery[cid] = 0.1
    m.mastery["classes-de-palavras"] = 0.95
    plan = build_plan(graph, m, targets=["crase"])
    names = [s.concept_id for s in plan.steps]
    assert "classes-de-palavras" not in names
    assert plan.skipped_mastered == 1
    pos = {cid: i for i, cid in enumerate(names)}
    for cid in names:
        for p in graph.prerequisites(cid):
            if p in pos:
                assert pos[p] < pos[cid]
    assert names[-1] == "crase"


def test_plan_is_empty_when_everything_is_mastered():
    m = LearnerModel(graph, mastery={cid: 0.95 for cid in graph.concepts})
    plan = build_plan(graph, m)
    assert plan.steps == [] and plan.weeks == 0
    assert all(p >= MASTERED_AT for p in m.mastery.values())


def test_plan_groups_steps_into_weeks():
    m = LearnerModel(graph, mastery={cid: 0.1 for cid in graph.concepts})
    plan = build_plan(graph, m, minutes_per_week=120)
    assert plan.weeks > 1
    for w in range(1, plan.weeks + 1):
        minutes = sum(s.est_minutes for s in plan.steps if s.week == w)
        assert minutes <= 120 + 60  # no máximo um passo estoura o limite semanal

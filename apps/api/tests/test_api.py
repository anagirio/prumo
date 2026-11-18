import pytest
from fastapi.testclient import TestClient

from prumo.main import create_app


@pytest.fixture()
def client():
    return TestClient(create_app(db_path=":memory:"))


def test_health_and_graph(client):
    assert client.get("/api/health").json()["concepts"] == 24
    g = client.get("/api/graph").json()
    assert len(g["concepts"]) == 24 and g["edges"]


def test_full_diagnosis_flow(client):
    lid = client.post("/api/learners").json()["learner_id"]
    answered = 0
    while True:
        nxt = client.post(f"/api/learners/{lid}/diagnosis/next").json()
        if nxt["done"]:
            break
        q = nxt["question"]
        assert "correct_option_id" not in q  # o gabarito não vaza antes da resposta
        r = client.post(
            f"/api/learners/{lid}/diagnosis/answer",
            json={"question_id": q["id"], "option_id": q["options"][0]["id"]},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["explanation"]
        if not body["correct"]:
            assert body["misconception"]
        answered += 1
        assert answered <= 12
    report = client.get(f"/api/learners/{lid}/report").json()
    assert report["questions_answered"] == answered
    plan = client.get(f"/api/learners/{lid}/plan").json()
    assert plan["steps"] or report["gaps"] == []
    if plan["steps"]:
        lesson = client.post(
            f"/api/learners/{lid}/lessons", json={"concept_id": plan["steps"][0]["concept_id"]}
        ).json()
        assert lesson["steps"]


def test_answering_twice_is_rejected(client):
    lid = client.post("/api/learners").json()["learner_id"]
    q = client.post(f"/api/learners/{lid}/diagnosis/next").json()["question"]
    payload = {"question_id": q["id"], "option_id": q["options"][0]["id"]}
    assert client.post(f"/api/learners/{lid}/diagnosis/answer", json=payload).status_code == 200
    assert client.post(f"/api/learners/{lid}/diagnosis/answer", json=payload).status_code == 409


def test_unknown_learner_and_invalid_inputs(client):
    assert client.get("/api/learners/nope/state").status_code == 404
    lid = client.post("/api/learners").json()["learner_id"]
    q = client.post(f"/api/learners/{lid}/diagnosis/next").json()["question"]
    bad = {"question_id": q["id"], "option_id": "zzz"}
    assert client.post(f"/api/learners/{lid}/diagnosis/answer", json=bad).status_code == 422
    assert client.get(f"/api/learners/{lid}/plan?targets=nao-existe").status_code == 404
    assert client.post(f"/api/learners/{lid}/lessons", json={"concept_id": "x"}).status_code == 404


def test_serve_static_front(tmp_path):
    from fastapi.testclient import TestClient

    from prumo.main import create_app

    (tmp_path / "index.html").write_text("<h1>prumo</h1>")
    import os

    os.environ["PRUMO_STATIC"] = str(tmp_path)
    try:
        client = TestClient(create_app(db_path=":memory:"))
        assert client.get("/").text == "<h1>prumo</h1>"
        assert client.get("/api/health").json()["ok"] is True
    finally:
        del os.environ["PRUMO_STATIC"]

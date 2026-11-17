"""API HTTP (FastAPI).

Rodar: uvicorn prumo.main:create_app --factory --reload --port 8000
(fábrica em vez de variável global: importar o módulo não cria banco de dados).
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from prumo.content import load_graph, load_question_bank
from prumo.diagnosis import DiagnosisEngine
from prumo.learner import LearnerModel
from prumo.llm import LessonRequest, LLMClient, make_llm_from_env
from prumo.models import DiagnosisReport, Lesson, Plan, PublicQuestion, Status
from prumo.planner import build_plan
from prumo.store import LearnerStore


class LearnerCreated(BaseModel):
    learner_id: str


class StateOut(BaseModel):
    answered: int
    mastery: dict[str, float]
    status: dict[str, Status]


class NextQuestionOut(BaseModel):
    done: bool
    question: PublicQuestion | None
    answered: int
    max_questions: int


class AnswerIn(BaseModel):
    question_id: str
    option_id: str


class AnswerOut(BaseModel):
    correct: bool
    correct_option_id: str
    explanation: str
    misconception: str | None
    suspects: list[str]
    state: StateOut


class LessonIn(BaseModel):
    concept_id: str


def create_app(
    db_path: str | None = None,
    llm: LLMClient | None = None,
    max_questions: int = 12,
) -> FastAPI:
    graph = load_graph()
    bank = load_question_bank(graph)
    engine = DiagnosisEngine(graph, bank, max_questions=max_questions)
    store = LearnerStore(db_path if db_path is not None else os.environ.get("PRUMO_DB", "prumo.db"))
    llm_client = llm or make_llm_from_env()

    app = FastAPI(title="Prumo API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("PRUMO_CORS", "http://localhost:5173").split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def load_model(learner_id: str) -> LearnerModel:
        data = store.load(learner_id)
        if data is None:
            raise HTTPException(404, "aluno não encontrado")
        return LearnerModel.from_dict(graph, data)

    def state_of(model: LearnerModel) -> StateOut:
        return StateOut(
            answered=len(model.history),
            mastery={c: round(p, 3) for c, p in model.mastery.items()},
            status=model.statuses(),
        )

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True, "concepts": len(graph.concepts), "questions": len(bank.all())}

    @app.get("/api/graph")
    def get_graph() -> dict:
        return graph.to_public()

    @app.post("/api/learners", response_model=LearnerCreated)
    def create_learner() -> LearnerCreated:
        return LearnerCreated(learner_id=store.create(LearnerModel(graph).to_dict()))

    @app.get("/api/learners/{learner_id}/state", response_model=StateOut)
    def get_state(learner_id: str) -> StateOut:
        return state_of(load_model(learner_id))

    @app.post("/api/learners/{learner_id}/diagnosis/next", response_model=NextQuestionOut)
    def next_question(learner_id: str) -> NextQuestionOut:
        model = load_model(learner_id)
        q = engine.next_question(model)
        return NextQuestionOut(
            done=q is None,
            question=PublicQuestion.from_question(q, graph.concepts[q.concept_id].name)
            if q
            else None,
            answered=len(model.history),
            max_questions=engine.max_questions,
        )

    @app.post("/api/learners/{learner_id}/diagnosis/answer", response_model=AnswerOut)
    def answer(learner_id: str, body: AnswerIn) -> AnswerOut:
        model = load_model(learner_id)
        try:
            q = bank.get(body.question_id)
        except KeyError:
            raise HTTPException(404, "questão não encontrada") from None
        if q.id in model.asked_question_ids():
            raise HTTPException(409, "questão já respondida")
        if body.option_id not in {o.id for o in q.options}:
            raise HTTPException(422, "alternativa inválida")
        fb = model.observe(q, body.option_id)
        store.save(learner_id, model.to_dict())
        return AnswerOut(
            correct=fb.correct,
            correct_option_id=q.correct_option_id,
            explanation=q.explanation,
            misconception=fb.misconception,
            suspects=fb.suspects,
            state=state_of(model),
        )

    @app.get("/api/learners/{learner_id}/report", response_model=DiagnosisReport)
    def report(learner_id: str) -> DiagnosisReport:
        return engine.report(load_model(learner_id))

    @app.get("/api/learners/{learner_id}/plan", response_model=Plan)
    def plan(
        learner_id: str,
        targets: str | None = Query(None, description="ids separados por vírgula"),
        minutes_per_week: int = Query(300, gt=0),
    ) -> Plan:
        model = load_model(learner_id)
        target_list = [t for t in targets.split(",") if t] if targets else None
        try:
            return build_plan(graph, model, target_list, minutes_per_week)
        except KeyError as e:
            raise HTTPException(404, f"conceito não encontrado: {e.args[0]}") from None

    @app.post("/api/learners/{learner_id}/lessons", response_model=Lesson)
    def lesson(learner_id: str, body: LessonIn) -> Lesson:
        model = load_model(learner_id)
        concept = graph.concepts.get(body.concept_id)
        if concept is None:
            raise HTTPException(404, "conceito não encontrado")
        wrong = [
            bank.get(h.question_id).option(h.option_id).misconception
            for h in model.history
            if not h.correct and h.concept_id == concept.id
        ]
        req = LessonRequest(
            concept=concept,
            prerequisite_names=[graph.concepts[p].name for p in graph.prerequisites(concept.id)],
            misconceptions=[m for m in wrong if m],
            mastery=model.mastery[concept.id],
        )
        return llm_client.lesson(req)

    return app

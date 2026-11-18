"""Camada de LLM, mantida nas bordas: o motor (grafo, diagnóstico, plano) nunca depende dela.

* MockLLM: determinístico, sem rede. Usado em testes e como plano B da demo.
* AnthropicLLM: gera aulas personalizadas. Se falhar por qualquer motivo, cai no MockLLM.

Variáveis de ambiente:
  PRUMO_LLM=anthropic        liga o provedor real (padrão: mock)
  ANTHROPIC_API_KEY=...      chave da API
  PRUMO_LLM_MODEL=...        modelo (padrão: claude-sonnet-5-5)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Protocol

from prumo.models import Concept, Lesson, LessonStep

# Corrigir poucos erros por vez: muita correção de uma só vez desanima o aluno.
MAX_ERRORS_PER_LESSON = 3


@dataclass
class LessonRequest:
    concept: Concept
    prerequisite_names: list[str] = field(default_factory=list)
    misconceptions: list[str] = field(default_factory=list)
    mastery: float = 0.5


class LLMClient(Protocol):
    def lesson(self, req: LessonRequest) -> Lesson: ...


class MockLLM:
    """Aula montada por template a partir do conteúdo curado."""

    def lesson(self, req: LessonRequest) -> Lesson:
        c = req.concept
        steps = [
            LessonStep(
                kind="prever",
                text=f"Antes de ler a explicação: o que você acha que é '{c.name}'? "
                "Escreva uma frase com suas palavras.",
            ),
            LessonStep(kind="explicar", text=c.description),
        ]
        if req.prerequisite_names:
            steps.append(
                LessonStep(
                    kind="revisar",
                    text="Isto se apoia em: " + ", ".join(req.prerequisite_names) + ".",
                )
            )
        for m in req.misconceptions[:MAX_ERRORS_PER_LESSON]:
            steps.append(LessonStep(kind="atencao", text=f"Vale ficar de olho: {m}"))
        steps.append(
            LessonStep(
                kind="verificar",
                text="Crie um exemplo seu e confira se ele segue a explicação acima.",
            )
        )
        return Lesson(concept_id=c.id, title=c.name, steps=steps, source="mock")


class AnthropicLLM:
    def __init__(self, model: str | None = None, api_key: str | None = None):
        import anthropic  # importado aqui para o pacote ser opcional

        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model or os.environ.get("PRUMO_LLM_MODEL", "claude-sonnet-5-5")
        self.fallback = MockLLM()

    def lesson(self, req: LessonRequest) -> Lesson:
        try:
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": self._prompt(req)}],
            )
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            data = json.loads(re.search(r"\{.*\}", text, re.DOTALL).group(0))  # type: ignore[union-attr]
            steps = [LessonStep(**s) for s in data["steps"]]
            return Lesson(
                concept_id=req.concept.id,
                title=data.get("title") or req.concept.name,
                steps=steps,
                source="llm",
            )
        except Exception:  # noqa: BLE001  (qualquer falha da API cai no plano B)
            return self.fallback.lesson(req)

    @staticmethod
    def _prompt(req: LessonRequest) -> str:
        errors = req.misconceptions[:MAX_ERRORS_PER_LESSON]
        return (
            "Você é um professor de Língua Portuguesa (português do Brasil) para concursos públicos, "
            "com tom simples e encorajador. Monte uma aula curta "
            f"sobre o conceito '{req.concept.name}'.\n"
            f"Resumo curado do conceito: {req.concept.description}\n"
            f"Pré-requisitos do aluno: {', '.join(req.prerequisite_names) or 'nenhum'}.\n"
            f"Domínio estimado do aluno (0 a 1): {req.mastery:.2f}.\n"
            f"Erros que o aluno cometeu: {'; '.join(errors) or 'nenhum registrado'}.\n"
            "Estrutura da aula, nesta ordem: (1) prever: um aquecimento que peça uma previsão; "
            "(2) explicar: explicação curta; (3) revisar: só se houver pré-requisito; "
            "(4) atencao: um passo por erro listado, explicando o motivo de forma simples e sem "
            "culpar o aluno; (5) exercicio: um exercício prático; (6) dica: uma dica que faça o "
            "aluno raciocinar, SEM entregar a resposta; (7) verificar: como o aluno confere a "
            "própria resposta. Nunca dê a resposta do exercício pronta. "
            "Apoie-se só no resumo curado e não invente regras gramaticais.\n"
            'Responda SOMENTE com JSON: {"title": str, "steps": [{"kind": one of '
            '"prever"|"explicar"|"revisar"|"atencao"|"exercicio"|"dica"|"verificar", "text": str}]}'
        )


def make_llm_from_env() -> LLMClient:
    if os.environ.get("PRUMO_LLM", "mock").lower() == "anthropic":
        try:
            return AnthropicLLM()
        except Exception:  # noqa: BLE001
            return MockLLM()
    return MockLLM()

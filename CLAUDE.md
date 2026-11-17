# CLAUDE.md

Contexto para sessões do Claude Code neste repositório.

## O que é

Prumo: tutor adaptativo de Português para concursos (Hack Brasil 2026, trilha Acesso à educação). Diagnóstico adaptativo sobre um grafo de pré-requisitos, plano pela base que falta, aulas por IA nas bordas.

## Comandos

```bash
make api-install && make web-install   # uma vez
make test                              # pytest (backend)
make api                               # uvicorn prumo.main:create_app --factory, porta 8000
make web                               # vite :5173
make simulate                          # avaliação com alunos sintéticos
make calibrate                         # recalibra parâmetros (treino/teste separados)
cd apps/api && .venv/bin/ruff check . && .venv/bin/ruff format .
cd apps/web && npm run build           # typecheck + build
```

## Princípios de design (não quebrar sem conversar)

1. **O motor é determinístico e testável.** `graph.py`, `learner.py`, `diagnosis.py` e `planner.py` não chamam LLM nem rede.
2. **LLM só nas bordas** (`llm.py`), sempre com plano B (`MockLLM`). A demo não pode depender de rede.
3. **Conteúdo é validado ao carregar** (`content.py`): toda alternativa errada descreve a concepção errada; suspeitos só podem ser pré-requisitos do conceito.
4. **Não afirmar mais do que a avaliação mostra.** A simulação valida a mecânica, não eficácia com pessoas.

## Regras do hackathon que afetam o código (detalhes em docs/HACKATHON_CHECKLIST.md)

- Todo o código vive neste repositório público novo, com commits feitos depois de 04/11 às 21h. **Nada de fork, nem de importar histórico.**
- **Não copiar código do LearnHarness** (AGPL-3.0). Só a ideia.
- Entrega até **30/11 às 23:59**. Depois disso o repositório fica **congelado até a final**: commit no período congelado pode desclassificar.
- O repositório precisa ficar público até pelo menos 15/12 e a demo precisa ficar online durante a avaliação.

## Convenções

- Python 3.11+, ruff (linha 100), tipos em tudo que for público. Português nos textos para o usuário; identificadores em português sem acento ou inglês, mas consistentes.
- Testes em `apps/api/tests`. Mudou o motor? Rode `make simulate` e `make calibrate` e confira se os números não pioraram. Nunca reporte resultado nos mesmos alunos usados para ajustar.
- Textos para o time: sem travessão longo; usar vírgula, dois-pontos ou ponto.

## Como adicionar conteúdo

1. Conceito novo em `apps/api/prumo/content/portugues.yaml` (id, nome, descrição, pré-requisitos, peso).
2. Pelo menos uma questão em `questoes_portugues.yaml`, **original** (não copiar prova de banca). Cada distrator: `misconception` e, quando fizer sentido, `suspect_prerequisites`.
3. `make test` valida a consistência (ciclos, suspeitos inválidos, gabarito inexistente).

## Para generalizar além do Português

O motor só conhece `Concept` e `Question`. Outra matéria = outros dois YAMLs e `load_graph(path)` / `load_question_bank(graph, path)`.

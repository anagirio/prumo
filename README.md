# Prumo

**Descubra o que falta antes de estudar o que cai.**

Tutor adaptativo de Língua Portuguesa para concursos públicos. Em vez de montar um cronograma por peso de matéria, o Prumo descobre o que a pessoa realmente entende, mapeia isso num grafo de pré-requisitos e ensina primeiro a base que falta.

Projeto do Hack Brasil 2026, trilha **Acesso à educação**.

> Nome de trabalho. Troque à vontade (procurem antes se já existe produto com o mesmo nome).

## O problema

Quem estuda sozinho para concurso recebe um edital com dezenas de tópicos e estuda "por matéria". Mas os conteúdos dependem uns dos outros: não dá para acertar reescrita de frases sem dominar crase, regência, pontuação e, por trás delas, orações subordinadas. Quando a pessoa erra, as plataformas mostram uma estatística ("você errou 40% de sintaxe"), mas não dizem **qual base está faltando**. Mentoria humana resolve isso, mas custa caro.

## A ideia

1. **Diagnóstico adaptativo:** poucas perguntas, cada uma escolhida pelo que mais revela. Cada alternativa errada está ligada a uma concepção errada e a um pré-requisito suspeito.
2. **Grafo de compreensão:** a crença sobre cada conceito é atualizada a cada resposta e propagada pelo grafo de pré-requisitos.
3. **Plano pela base:** o que falta de fundamento vem antes do que depende dele.
4. **Aula sob medida:** a IA monta a aula a partir do que a pessoa já domina e dos erros que cometeu (o motor é determinístico; a IA fica só nas bordas).

A inspiração conceitual vem de projetos de "agent harness for learning", como o LearnHarness. **Nenhum código foi copiado** (a licença dele é AGPL-3.0 e o regulamento exige repositório novo).

## Rodando

Pré-requisitos: Python 3.11+ e Node 20+.

```bash
make api-install     # cria venv e instala o backend
make web-install     # instala o frontend
make test            # roda os testes do backend
make api             # API em http://localhost:8000  (docs em /docs)
make web             # frontend em http://localhost:5173
make simulate        # compara o diagnóstico com baselines em alunos sintéticos
make calibrate       # recalibra os parâmetros (treino/teste separados, ~6 min)
```

Sem `make`: veja os comandos no `Makefile`.

## Colocando no ar

Um `Dockerfile` na raiz compila o front e a API serve tudo (um container, um link). Passo a passo em `docs/DEPLOY.md` (Render, via `render.yaml`). Teste local: `make docker`.

Aulas por IA (opcional): `pip install -e "apps/api[llm]"` e exporte `PRUMO_LLM=anthropic` e `ANTHROPIC_API_KEY=...`. Sem isso, a API usa aulas por template (`MockLLM`), e a demo nunca depende de rede.

## Estrutura

```
apps/api/prumo/
  graph.py       grafo de pré-requisitos (DAG), ancestrais/descendentes, validações
  learner.py     modelo de crença do aluno (Bayes + propagação no grafo)
  diagnosis.py   escolha da próxima pergunta e relatório de lacunas-raiz
  planner.py     plano de estudo respeitando pré-requisitos
  content/       grafo de Português e questões originais (YAML)
  llm.py         camada de IA (mock e Anthropic), só nas bordas
  simulation.py  alunos sintéticos para avaliar a mecânica
  main.py        API FastAPI (e serve o front compilado em produção)
apps/web/        Vite + React + TypeScript
Dockerfile       build único (front + API); render.yaml é o blueprint do Render
docs/            arquitetura, avaliação, roadmap, checklist do regulamento
```

## Estado atual

Funciona de ponta a ponta com 24 conceitos e 28 questões de Português: diagnóstico, relatório com grafo, plano, aula e exercício com dica (a pista mostra o raciocínio por trás da alternativa errada, sem entregar a resposta). Roda sem IA; com IA, a aula segue a estrutura aquecimento, explicação, exercício, dica e verificação. **Veja `docs/PROXIMOS_PASSOS.md` (passo a passo) e `docs/ROADMAP.md` (dia a dia) para o que fazer até 30/11** e `docs/EVALUATION.md` para o que a simulação mostra e o que ela não prova.

## Limitações assumidas

- O grafo de dependências e os pesos são **hipóteses de trabalho**: precisam de validação com professor e provas anteriores.
- Há 1 questão por conceito, e 2 nos quatro conceitos de base. Com chute de 25%, uma questão só dá evidência fraca.
- As métricas de simulação validam a mecânica, **não** a eficácia com pessoas reais. O piloto com concurseiros é o que prova.

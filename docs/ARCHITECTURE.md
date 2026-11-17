# Arquitetura

## Visão geral

```
        navegador (React)                                   servidor (FastAPI)
  ┌────────────────────────┐   /api/*    ┌──────────────────────────────────────────┐
  │ Quiz · Relatório · Plano│ ─────────▶ │ main.py (rotas)                          │
  │ GraphView (SVG)         │ ◀───────── │   │                                      │
  └────────────────────────┘             │   ├─ DiagnosisEngine  (escolhe pergunta) │
                                         │   ├─ LearnerModel     (crença + grafo)   │
                                         │   ├─ build_plan       (ordem por base)   │
                                         │   ├─ QuestionBank/KnowledgeGraph (YAML)  │
                                         │   ├─ LearnerStore     (SQLite)           │
                                         │   └─ LLMClient        (Mock | Anthropic) │
                                         └──────────────────────────────────────────┘
```

Núcleo determinístico no meio; IA e rede apenas na borda (`llm.py`).

## Conceitos de domínio

- **Concept**: algo a entender (ex.: "Crase"). Tem pré-requisitos, tópicos de edital e um peso estimado.
- **Grafo**: DAG onde a aresta aponta do pré-requisito para o dependente. Validado na carga (ciclos, ids inexistentes).
- **Question**: pergunta de múltipla escolha ligada a um conceito. Cada alternativa errada guarda a **concepção errada** que revela e os **pré-requisitos suspeitos**. Esse é o diferencial: o erro vira diagnóstico, não só estatística.

## Modelo do aluno (`learner.py`)

Crença `p(c)` de domínio por conceito, começando em 0,5.

Resposta sobre o conceito `c` (chute `g = 1/nº de alternativas`, deslize `s = 0,10`):

- acerto: `p' = p(1-s) / (p(1-s) + (1-p)g)`
- erro: `p' = ps / (ps + (1-p)(1-g))`

Propagação pelo grafo (heurísticas explícitas, constantes no topo do arquivo):

- **Acerto**: cada pré-requisito a distância `d` sobe `post * 0,6 * 0,5^d` da distância até 1.
- **Erro**: pré-requisitos suspeitos da alternativa escolhida caem pela metade; demais pré-requisitos diretos caem 15%; dependentes caem até 25% (menos quanto mais longe).
- **Culpa por inferência não vira lacuna sozinha**: um pré-requisito que nunca foi perguntado é limitado a 0,36 (acima do limite de lacuna, 0,35). Ele precisa ser testado para ser classificado. Sem isso, o motor inventava lacunas-raiz falsas (bug encontrado na simulação).

Classificação: `dominado` (p ≥ 0,70), `lacuna` (p ≤ 0,35), `incerto` (entre os dois).

## Escolha da próxima pergunta (`diagnosis.py`)

Entre conceitos `incerto` com pergunta ainda não feita, escolhe o de maior

```
incerteza(4p(1-p)) × (1 + 0,02·alcance) × (1 + 2·dependentes em lacuna) × (1 + 1·suspeito) × peso
```

Os dois bônus fazem o motor **descer em direção à raiz**: depois de uma falha, sonda os pré-requisitos incertos dela, principalmente os que as alternativas erradas apontaram como suspeitos. Para quando tudo está classificado ou o orçamento de perguntas (padrão 12) acaba.

**Relatório**: dominados, lacunas, incertos, **lacunas-raiz** (lacuna sem pré-requisito em lacuna, ordenadas por quantos conceitos destravam) e as concepções erradas observadas.

## Plano (`planner.py`)

Escopo = alvos + todos os pré-requisitos. Pendente = abaixo de 0,70. Ordenação topológica por prioridade `peso × (1 + 0,2 × dependentes pendentes)`, então a base que destrava mais coisas vem antes. Passos são agrupados em semanas por minutos disponíveis. Cada passo traz motivo e o que o bloqueia.

## API

| Método | Rota | Função |
|---|---|---|
| GET | `/api/health` | contagem de conceitos e questões |
| GET | `/api/graph` | conceitos, arestas e profundidade |
| POST | `/api/learners` | cria aluno (id anônimo) |
| GET | `/api/learners/{id}/state` | crença e status por conceito |
| POST | `/api/learners/{id}/diagnosis/next` | próxima pergunta (sem gabarito) |
| POST | `/api/learners/{id}/diagnosis/answer` | registra resposta, devolve explicação e diagnóstico |
| GET | `/api/learners/{id}/report` | relatório do diagnóstico |
| GET | `/api/learners/{id}/plan` | plano (`targets`, `minutes_per_week`) |
| POST | `/api/learners/{id}/lessons` | aula do conceito |

Documentação interativa em `/docs` com a API rodando.

## Pontos de extensão

- **Prática sem nomear o conceito** (ainda não implementada): gerar problemas que exijam o conhecimento certo e dar dicas conforme o raciocínio. Entra em `llm.py` + nova rota.
- **Mais de uma questão por conceito**: o motor já aceita; o diagnóstico usa a próxima não feita.
- **Outra matéria**: novos YAMLs, mesmo motor.
- **Memória de longo prazo**: o estado já é persistido; falta reaproveitar entre editais e sessões.

## Limitações conhecidas

- Constantes do modelo são heurísticas ajustadas na simulação, não aprendidas com dados reais.
- A simulação gera alunos com a mesma hipótese estrutural do motor; ver `EVALUATION.md`.
- Sem autenticação: o id do aluno é um token opaco. Para o piloto, não coletar dado pessoal.

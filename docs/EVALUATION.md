# Avaliação

## O que medimos e o que não medimos

`make simulate` gera **alunos sintéticos** e compara três estratégias de diagnóstico com o mesmo orçamento de perguntas:

1. **Adaptativo**: grafo + próxima pergunta escolhida pelo motor.
2. **Aleatório com propagação**: perguntas sorteadas, mas com o mesmo grafo.
3. **Aleatório sem grafo**: perguntas sorteadas e cada conceito tratado isolado.

Cada aluno sintético tem lacunas-raiz sorteadas; todos os dependentes delas também são desconhecidos; há ruído por conceito; chute de 1/4 quando não sabe e deslize quando sabe. Para testar robustez, há **5 populações** (`prumo/simulation.py`, `POPULATIONS`): padrão (1 a 3 raízes, 5% de ruído, 10% de deslize), ruidosa (15% de ruído), desatenta (20% de deslize), muitas lacunas (até 5 raízes) e poucas lacunas (1 raiz, 2% de ruído).

**Limite importante:** o aluno sintético segue a mesma hipótese estrutural que o motor assume (lacuna na base derruba o que depende dela). Isso valida a **mecânica**, isto é, se o motor aproveita bem um orçamento curto de perguntas. **Não prova** que o diagnóstico acerta com pessoas reais. Quem prova isso é o piloto (abaixo).

Métricas: "desconhecido" é a classe positiva (crença < 0,5). Lacunas-raiz: revocação e precisão contra as raízes verdadeiras sorteadas.

## Calibração e resultados

`make calibrate` roda `scripts/calibrate.py`, que corrige um erro da primeira versão deste documento: os parâmetros eram ajustados e reportados **nos mesmos alunos sintéticos**, o que inflava o ganho. Agora:

- os 10 parâmetros do motor (`learner.py` e `diagnosis.py`) são escolhidos só com **8 sementes de treino** (200 alunos cada), na média das 5 populações, por busca coordenada (um parâmetro por vez, 2 rodadas);
- um parâmetro só muda se o ganho no treino passar de 0,002 (evita perseguir ruído);
- o resultado é medido em **20 sementes de teste** (300 alunos cada), nunca vistas no ajuste, com erro-padrão entre sementes;
- critério único (objetivo) = média entre o F1 de "desconhecido" e o F1 de lacunas-raiz, 12 perguntas.

Resultado completo em `docs/calibration_result.json`.

### Antes da calibração (parâmetros iniciais), teste

| População | Adaptativo | Aleat. + propagação | Aleat. sem grafo | Adaptativo menos aleat. + prop. |
|---|---|---|---|---|
| padrão | 0,502 ± 0,004 | 0,461 | 0,407 | +0,041 ± 0,005 |
| ruidosa | 0,452 ± 0,004 | 0,464 | 0,435 | **-0,012 ± 0,005** |
| desatenta | 0,430 ± 0,004 | 0,417 | 0,359 | +0,013 ± 0,004 |
| muitas lacunas | 0,507 ± 0,003 | 0,479 | 0,415 | +0,028 ± 0,004 |
| poucas lacunas | 0,453 ± 0,004 | 0,382 | 0,345 | +0,072 ± 0,006 |

Ou seja: a vantagem da seleção adaptativa que eu havia reportado (+0,03 de F1) era frágil e **sumia** com alunos ruidosos.

### Depois da calibração, teste

| População | Adaptativo | Aleat. + propagação | Aleat. sem grafo | Adaptativo menos aleat. + prop. |
|---|---|---|---|---|
| padrão | **0,553 ± 0,003** | 0,473 | 0,407 | +0,079 ± 0,004 |
| ruidosa | **0,515 ± 0,003** | 0,477 | 0,435 | +0,038 ± 0,004 |
| desatenta | **0,472 ± 0,003** | 0,426 | 0,359 | +0,046 ± 0,004 |
| muitas lacunas | **0,569 ± 0,002** | 0,492 | 0,415 | +0,077 ± 0,004 |
| poucas lacunas | **0,519 ± 0,005** | 0,389 | 0,345 | +0,130 ± 0,006 |

População padrão, detalhe: F1 de "desconhecido" 0,655 (adaptativo), 0,594 (aleat. + propagação), 0,463 (sem grafo); lacunas-raiz: revocação 0,42 e precisão 0,49 no adaptativo.

Parâmetros que mudaram: `SLIP` 0,10 para 0,05, `SUSPECT_FACTOR` 0,5 para 0,7, `DEPENDENT_PENALTY` 0,25 para 0,4, `MASTERED_AT` 0,7 para 0,6, `REACH_WEIGHT` 0,02 para 0, `GAP_DESCENT_BONUS` 2 para 1, `SUSPECT_BONUS` 1 para 2. Os demais ficaram.

### Leitura honesta

- **O grafo continua sendo o que mais ajuda** (F1 de 0,46 sem grafo para 0,59 com grafo e sorteio, 0,66 com seleção adaptativa, população padrão). Esse é o argumento central.
- **Agora a seleção adaptativa vence o sorteio com propagação em todas as 5 populações**, com margem de 0,04 a 0,13 de objetivo e erro-padrão abaixo de 0,01. Antes da calibração isso não era verdade.
- **Calibrar não é só ajustar parâmetros: as probabilidades não são calibradas como chance real.** O erro de calibração esperado (ECE) é ~0,17 e o Brier ~0,16. O motor superestima a chance de "não sabe" nas faixas do meio (previsto 0,5, real 0,23) porque o prior é 0,5 e, na simulação, só 31% dos conceitos são desconhecidos. Mudar o prior para corrigir isso quebra a lógica de classificação (conceitos não testados passariam a "dominados"). Decisão: **a interface não mostra percentual**; mostra só o status (dominado, lacuna, na dúvida), que é o que o motor sustenta.
- **Otimismo que permanece:** o aluno sintético compartilha a hipótese estrutural do motor, e quatro dos parâmetros escolhidos estão na borda da grade testada (`SLIP`, `DEPENDENT_PENALTY`, `MASTERED_AT`, `REACH_WEIGHT`), então o ótimo pode estar além. `SLIP` 0,05 é **menor** do que o deslize real esperado de concurseiros cansados; revisar com os dados do piloto.
- **A revocação de lacunas-raiz ainda é baixa (~0,42).** A causa principal é o chute (25% de acerto sem saber) com 1 questão por conceito. A saída é mais de uma questão nos conceitos de base.

### Histórico de ajustes (para não repetir erros)

1. Primeira versão: um teste de relatório falhou (o motor apontava `coordenacao`, um pré-requisito nunca testado, como lacuna-raiz). Causa: a culpa por inferência derrubava pré-requisitos nunca testados até "lacuna". Correção: culpa inferida limitada a 0,36.
2. Bônus para sondar pré-requisitos incertos de um conceito que falhou e os apontados como suspeitos pelas alternativas erradas. Pesos escolhidos à mão e conferidos na mesma semente usada para reportar (erro que a calibração acima corrige).
3. Calibração com treino e teste separados, 5 populações e erro-padrão (esta seção).

## Como validar com pessoas reais (piloto)

Meta: 5 a 10 concurseiros entre 25/11 e 28/11.

1. Cada pessoa faz o diagnóstico adaptativo (12 perguntas).
2. Depois responde **todas as 28 questões** (teste completo, que serve de referência).
3. Medir: concordância por conceito entre o diagnóstico curto e o teste completo; tempo gasto; nota de utilidade do plano (1 a 5) e uma frase livre sobre "isso reflete o que eu sei?".
4. Pedir também a autoavaliação antes de começar, para comparar com o diagnóstico.
5. Registrar tudo anonimamente (o id do aluno é aleatório). **Não coletar nome, e-mail nem outro dado pessoal.** Avisar que é um teste de um projeto de hackathon.

Reportar o que vier, inclusive se for ruim. Resultado real, mesmo modesto, pesa mais para a banca do que promessa.

## Reproduzir

```bash
cd apps/api
python scripts/simulate_students.py --students 500 --max-questions 12 --seed 7
```

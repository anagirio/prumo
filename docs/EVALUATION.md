# Avaliação

## O que medimos e o que não medimos

`make simulate` gera **alunos sintéticos** e compara três estratégias de diagnóstico com o mesmo orçamento de perguntas:

1. **Adaptativo**: grafo + próxima pergunta escolhida pelo motor.
2. **Aleatório com propagação**: perguntas sorteadas, mas com o mesmo grafo.
3. **Aleatório sem grafo**: perguntas sorteadas e cada conceito tratado isolado.

Cada aluno sintético tem 1 a 3 lacunas-raiz sorteadas; todos os dependentes delas também são desconhecidos; 5% de ruído por conceito; chute de 1/4 quando não sabe; deslize de 10% quando sabe.

**Limite importante:** o aluno sintético segue a mesma hipótese estrutural que o motor assume (lacuna na base derruba o que depende dela). Isso valida a **mecânica**, isto é, se o motor aproveita bem um orçamento curto de perguntas. **Não prova** que o diagnóstico acerta com pessoas reais. Quem prova isso é o piloto (abaixo).

Métricas: "desconhecido" é a classe positiva (crença < 0,5). Lacunas-raiz: revocação e precisão contra as raízes verdadeiras sorteadas.

## Resultados (500 alunos, seed 7)

Orçamento de 12 perguntas (24 conceitos, 1 questão por conceito):

| Estratégia | Acurácia | Precisão | Revocação | F1 | Raiz: revocação | Raiz: precisão |
|---|---|---|---|---|---|---|
| Adaptativo | 0,823 | 0,652 | 0,645 | **0,611** | 0,352 | **0,442** |
| Aleatório com propagação | 0,787 | 0,580 | 0,662 | 0,580 | 0,341 | 0,397 |
| Aleatório sem grafo | 0,779 | 0,713 | 0,388 | 0,471 | 0,379 | 0,385 |

Variando o orçamento (F1):

| Perguntas | Adaptativo | Aleatório + propagação | Aleatório sem grafo |
|---|---|---|---|
| 8 | 0,510 | 0,514 | 0,343 |
| 12 | 0,611 | 0,580 | 0,471 |
| 16 | 0,672 | 0,619 | 0,554 |

Com outra semente (99, 12 perguntas), o adaptativo fica em F1 0,630 contra 0,588 e 0,466.

### Leitura honesta

- **O grafo é o que mais ajuda.** Com 12 perguntas, propagar pelo grafo sobe o F1 de 0,47 para 0,58 (ou 0,61 com seleção adaptativa). Esse é o argumento central do projeto.
- **A seleção adaptativa ajuda menos:** +0,03 de F1 sobre sortear com propagação com 12 perguntas, +0,05 com 16, e **empata com 8**. Vale como refinamento, não como milagre.
- **A revocação de lacunas-raiz é baixa (~0,35)** em todas as estratégias com 1 questão por conceito. A causa principal é o chute: 25% das vezes quem não sabe acerta, e uma questão só não desfaz isso. A saída é mais de uma questão por conceito nos conceitos de base (ver roadmap).

### Histórico de ajustes (para não repetir erros)

1. Primeira versão: um teste de relatório falhou (o motor apontava `coordenacao`, um pré-requisito nunca testado, como lacuna-raiz) e a simulação mostrou revocação de raízes baixa (0,19 contra 0,30 sem grafo, com 10 perguntas e 120 alunos). Causa: a culpa por inferência derrubava pré-requisitos nunca testados até "lacuna", e o motor nunca os sondava.
2. Correção A: a culpa por inferência fica limitada a 0,36 (o conceito precisa ser testado para virar lacuna). O teste passou, mas o adaptativo ainda ficava **abaixo** de sortear com propagação (F1 0,558 contra 0,580; raiz 0,242 contra 0,341; 12 perguntas, 500 alunos).
3. Correção B: bônus para sondar os pré-requisitos incertos de um conceito que falhou e os apontados como suspeitos pelas alternativas erradas. Pesos escolhidos por varredura na simulação. Resultado: os números da tabela acima.

Os pesos foram ajustados nos mesmos alunos sintéticos usados para reportar, então a melhora sobre o sorteio com propagação tem algum otimismo. A semente 99 (não usada no ajuste) mostra a mesma ordem das estratégias.

## Como validar com pessoas reais (piloto)

Meta: 5 a 10 concurseiros entre 25/11 e 28/11.

1. Cada pessoa faz o diagnóstico adaptativo (12 perguntas).
2. Depois responde **todas as 24 questões** (teste completo, que serve de referência).
3. Medir: concordância por conceito entre o diagnóstico curto e o teste completo; tempo gasto; nota de utilidade do plano (1 a 5) e uma frase livre sobre "isso reflete o que eu sei?".
4. Pedir também a autoavaliação antes de começar, para comparar com o diagnóstico.
5. Registrar tudo anonimamente (o id do aluno é aleatório). **Não coletar nome, e-mail nem outro dado pessoal.** Avisar que é um teste de um projeto de hackathon.

Reportar o que vier, inclusive se for ruim. Resultado real, mesmo modesto, pesa mais para a banca do que promessa.

## Reproduzir

```bash
cd apps/api
python scripts/simulate_students.py --students 500 --max-questions 12 --seed 7
```

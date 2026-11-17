# Revisão de conteúdo (17/11)

Primeira rodada de revisão do grafo (`portugues.yaml`) e das 24 questões (`questoes_portugues.yaml`), feita por IA, sem skill de gramática. **Não substitui um professor ou aprovado em concurso.** Quem validar deve focar nas seções "Dúvidas para o especialista" e "Mudanças de grafo sugeridas".

## O que eu conferi e está certo

- **Os 24 gabaritos**, um por um: nenhum erro de gramática encontrado. Cada questão tem uma única alternativa correta pela norma-padrão.
- Pontos que costumam gerar polêmica e estão tratados de forma conservadora: `assistir ao filme` (norma-padrão exige a preposição), `pois` explicativo antes da oração e conclusivo depois do verbo, `ideia` sem acento (Acordo de 1990), `leem` sem circunflexo, concordância de `anexo`, `mesmo` e `bastante`.
- As descrições dos conceitos (`description`, que alimentam a aula por IA) não contêm regra errada.

## O que eu corrigi (já aplicado)

1. **Posição do gabarito.** 21 das 24 respostas certas estavam em A ou B (A: 10, B: 11, C: 2, D: 1). Quem chutasse A ou B sempre acertaria cerca de 87% das vezes, o que também enviesa o diagnóstico (o chute deixa de ser 1/4). Agora são 6 respostas por letra, sem três iguais seguidas. O texto, o erro descrito em cada alternativa e o gabarito de cada questão foram conferidos por script e não mudaram, só a ordem.
2. **Pré-requisito suspeito de `q-pontuacao-1`.** A alternativa "O fiscal, verificou os documentos..." (vírgula entre sujeito e verbo) apontava `coordenacao`; o certo é `sujeito-predicado`.

## Dúvidas para o especialista

1. `q-conjuncoes-1` testa só conjunção, embora o conceito se chame "Preposições e conjunções". Uma pessoa pode saber conjunção e não preposição. Vale separar em dois conceitos?
2. `q-coordenacao-1`: "pois o prazo é curto" como **explicativa** (não causal). É a leitura mais comum, mas algumas bancas aceitam a leitura causal. Se o professor preferir, trocar por "porque", que é inequívoco.
3. Cada conceito tem **uma questão só**. Isso limita a detecção da base que falta (revocação das lacunas-raiz ~0,42 na simulação). Prioridade: segunda questão em `classes-de-palavras`, `sujeito-predicado`, `preposicoes-conjuncoes` e `pronomes`.
4. Os **pesos** (`weight`) são palpite. Pedir ao especialista que ordene por frequência real nas bancas-alvo (CESPE/Cebraspe, FGV, VUNESP...) e dizer em qual banca focar, porque o estilo muda muito.
5. `interpretacao-ideia-central` é um único conceito com peso 1,5, mas interpretação de texto é, nas bancas, a maior parte das questões de Português. Provavelmente precisa virar vários conceitos (inferência, ideia central, tipologia e gêneros, figuras de linguagem, intertextualidade).

## Mudanças de grafo sugeridas (não aplicadas)

Mudar o grafo exige rodar `make calibrate` de novo e conferir o impacto. Por isso deixei como sugestão para o especialista aprovar:

| Conceito | Hoje depende de | Sugestão | Por quê |
|---|---|---|---|
| `ortografia` | `acentuacao` | sem pré-requisito | acentuação e grafia de palavras são independentes na prática |
| `subordinacao-adjetiva` | `subordinacao-substantiva`, `pronomes` | `pronomes`, `termos-acessorios`, `coordenacao` | o que sustenta a adjetiva é o pronome relativo e o adjunto adnominal, não a substantiva |
| `subordinacao-adverbial` | `subordinacao-substantiva`, `termos-acessorios` | `termos-acessorios`, `preposicoes-conjuncoes`, `coordenacao` | depende das conjunções subordinativas e do adjunto adverbial |
| `pontuacao` | `coordenacao`, `subordinacao-adverbial`, `termos-acessorios` | acrescentar `subordinacao-adjetiva` | a descrição cita adjetivas explicativas entre vírgulas |
| `funcoes-que-se` | `pronomes`, `preposicoes-conjuncoes`, `subordinacao-substantiva` | acrescentar `subordinacao-adjetiva` | o "que" relativo é o caso mais cobrado |
| `colocacao-pronominal` | `pronomes`, `flexao-verbal` | acrescentar `preposicoes-conjuncoes` | a próclise depende de conjunções subordinativas e advérbios |
| `reescrita-frases` | `pontuacao`, `concordancia-verbal`, `regencia-verbal`, `crase`, `colocacao-pronominal` | acrescentar `subordinacao-adverbial` e `coesao-referenciacao` | a questão de reescrita testa troca de conectivo |

## Lacunas de cobertura (conceitos que faltam em editais típicos)

Vozes verbais (ativa, passiva, passiva sintética), orações reduzidas, regência nominal, emprego dos porquês, emprego do hífen, pronomes de tratamento, figuras de linguagem, tipologia e gêneros textuais, paralelismo, formação de palavras. Não precisam entrar todos no hackathon: escolham 3 a 5 pelo peso nas bancas e deixem o resto no roadmap.

## Como fechar a validação

1. Entregar este arquivo, o `portugues.yaml` e o `questoes_portugues.yaml` a um professor de cursinho ou aprovado.
2. Pedir que responda: (a) algum gabarito está discutível? (b) a ordem de dependência faz sentido? (c) quais conceitos mais caem na banca-alvo?
3. Registrar o nome e a data da validação no README (com autorização da pessoa). Isso entra no pitch como "conteúdo validado por especialista".

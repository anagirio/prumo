# Próximos passos (a partir de terça, 17/11)

Tudo em ordem de prioridade. O que está marcado com ⏰ tem prazo duro do hackathon.

## Hoje à noite (30 minutos)

1. **Conferir que tudo roda no seu Mac.**
   ```
   cd ~/development/prumo
   make api-install web-install test
   make api          # terminal 1
   make web          # terminal 2, abrir http://localhost:5173
   ```
2. **Commit e push** do visual novo e da calibração:
   ```
   git add -A
   git commit -m "feat: visual de caderno e calibracao com treino/teste separados"
   git push
   ```
3. **Conferir que o repositório está público** (selo "Public" em github.com/anagirio/prumo) e que o CI ficou verde na aba Actions.
4. ⏰ **Chamar as outras duas** como colaboradoras (Settings, Collaborators) e mandar o link do repositório.
5. **Conversa sem pressa com as duas:** só quem chegar à final vai a São Paulo (finalistas saem em 2/12, confirmação até 4/12 às 23h59, todos do time precisam ir, custos por conta de cada um). Se alguma já sabe que não pode, melhor dizer cedo.

## Esta semana: até sexta 20/11 (marco M1)

6. **Validar o grafo com especialista.** Procure alguém que domine Português para concursos (professor de cursinho, aprovado, monitor) e mostre `apps/api/prumo/content/portugues.yaml`. Perguntas para ele: as dependências fazem sentido? Os pesos refletem o que cai nas provas? Alguma questão tem gabarito discutível? Sem isso, o diagnóstico é uma hipótese.
7. **Colocar o app online** (front e API). Escolham hospedagens gratuitas que preferirem e testem o fluxo completo pelo link público. ⏰ A demo online é requisito da entrega.
8. **Segunda questão nos conceitos de base** (`classes-de-palavras`, `sujeito-predicado`, `preposicoes-conjuncoes`, `pronomes`). É o que mais melhora a detecção da base que falta (revocação das raízes está em ~0,42 por causa do chute). Depois rode `make simulate` e anote a diferença.
9. **Teste com 2 pessoas de fora do time**, vendo se entendem o mapa sem explicação.

## Semana que vem: 21/11 a 27/11

10. **Módulo de prática** (problemas que exigem o conhecimento certo, com dica conforme o erro), reaproveitando `llm.py`.
11. **Aulas por IA** com checagem contra a `description` curada, para a IA não inventar regra gramatical.
12. **Piloto com 5 a 10 concurseiros** (protocolo em `docs/EVALUATION.md`). Sem coletar nome nem e-mail. É a única prova de que funciona com gente real.
13. **State Space Model como modelo alternativo** (opcional, só depois do M1). Implementar ao lado do modelo atual e comparar com `make calibrate`. Entra no pitch como diferencial técnico se ganhar, e como "trabalho futuro" se não ganhar. Não bloqueia nada.
14. ⏰ **Sexta 27/11 à noite: congelar funcionalidades.** Daí em diante, só correção de bug.

## Fim de novembro: 28/11 a 30/11

15. **Gravar o vídeo de 3 minutos** seguindo `docs/DEMO_SCRIPT.md` (português ou inglês). Use os números reais do piloto.
16. **Revisar o repositório:** README claro, LICENSE, sem chaves de API nem arquivos pessoais, histórico começando depois de 4/11 às 21h.
17. ⏰ **Submeter até segunda 30/11 às 18h** (o prazo é 23h59, a margem é de segurança): repositório público, demo online, vídeo.
18. ⏰ Depois da entrega: **código congelado**. Commits depois de 30/11 às 23h59 podem desclassificar, mesmo se vocês forem finalistas (a final presencial é em 12/12, em São Paulo, e o desenvolvimento só retoma lá). O repositório precisa ficar público até 15/12.

## Regras que valem sempre

- Todo resultado de avaliação vem de alunos que o modelo **não viu** durante o ajuste (`make calibrate` já faz isso).
- Diga no pitch o que é simulação e o que é piloto real. Os juízes percebem quando se mistura.
- A interface não mostra percentual de "domínio": o modelo ordena e classifica bem, mas as probabilidades não são calibradas como chance real (explicação em `docs/EVALUATION.md`).

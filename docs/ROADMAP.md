# Roadmap até 30/11

Hoje é terça, 17/11. Entrega em **13 dias**. Quatro critérios pesam igual: execução, implementação, impacto e comunicação. O plano reserva tempo para os quatro.

## Papéis sugeridos (ajustem como quiserem)

- **A, Motor e avaliação:** `learner`, `diagnosis`, `planner`, simulação, testes, README técnico.
- **B, Conteúdo e IA:** questões, validação pedagógica do grafo, aulas e prática com LLM.
- **C, Produto e comunicação:** frontend, deploy, piloto com usuários, vídeo e pitch.

## Marcos

| Marco | Data | O que precisa estar de pé |
|---|---|---|
| M1 | Sex 20/11 | Diagnóstico ponta a ponta **online** (front + API no ar) |
| M2 | Ter 24/11 | Aula e prática funcionando; 2 questões nos conceitos de base |
| M3 | Qui 26/11 | Piloto com concurseiros em andamento, dados sendo coletados |
| Freeze | Sex 27/11 à noite | Congelamento de funcionalidades; só correções |
| Entrega | Seg 30/11 | Submetido até as 18h (margem de 6h) |

## Dia a dia

**Ter 17/11 (hoje)**
- Todos: rodar o projeto (`make api-install web-install test`), ler `docs/HACKATHON_CHECKLIST.md`.
- **Criar o repositório público novo no GitHub e subir o código** (é um repositório novo, com todos os commits de agora em diante). Adicionar `LICENSE`.
- Confirmar que os 3 podem ir a São Paulo em 12/12.
- Decidir nome definitivo.

**Qua 18/11**
- A: revisar parâmetros do modelo; adicionar suporte a 2ª questão por conceito no teste da simulação.
- B: validar o grafo com **uma pessoa que domine Português para concursos** (professor, aprovado). Corrigir dependências e pesos. Começar as questões 2 dos conceitos de base.
- C: deploy preliminar (front e API). Escolham hospedagens gratuitas de sua preferência e confirmem que a demo fica online.

**Qui 19/11**
- A: reduzir chute: usar 2 questões nos conceitos de base (`classes-de-palavras`, `sujeito-predicado`, `preposicoes-conjuncoes`, `pronomes`). Rodar `make simulate` e registrar a diferença.
- B: continuar questões originais; checar cada gabarito duas vezes.
- C: polir o quiz e o relatório; versão mobile.

**Sex 20/11 (M1)**
- Fluxo completo online. Teste com 2 pessoas de fora do time.

**Sáb 21/11 e Dom 22/11**
- A: módulo de **prática** (problemas que exigem o conhecimento certo, sem nomear o conceito; dica conforme o erro). Reaproveita `llm.py`.
- B: prompts das aulas por IA, com checagem contra `description` curada para a IA não inventar regra gramatical.
- C: telas de aula e prática; ensaiar o fluxo da demo.

**Seg 23/11**
- Integração. Tratamento de erro e estados vazios. Plano B da demo (modo sem IA já existe).

**Ter 24/11 (M2)**
- Aula + prática no ar. Recrutar 5 a 10 concurseiros para o piloto.

**Qua 25/11 e Qui 26/11 (M3)**
- Piloto: protocolo em `docs/EVALUATION.md`. Registrar concordância diagnóstico vs teste completo, tempo e utilidade.
- A: ajustar pesos só se os dados reais justificarem.

**Sex 27/11**
- Calibração final com dados do piloto. **Congelar funcionalidades à noite.**

**Sáb 28/11**
- README final, diagrama de arquitetura, resultados do piloto. Gravar o vídeo (roteiro em `docs/DEMO_SCRIPT.md`).

**Dom 29/11**
- Vídeo final. Revisar o checklist. Teste de carga leve na demo. Verificar que o repositório está público e sem segredos.

**Seg 30/11**
- **Submeter até as 18h.** Depois disso, nada de commit até a final.

## Depois da entrega

- 02/12: finalistas. Preparar slides e pitch sem mexer no repositório.
- 04/12 às 23:59: confirmar presença.
- 12/12: final em São Paulo.
- Manter repositório público e demo online até 15/12.

## Riscos e planos B

| Risco | Plano B |
|---|---|
| API de LLM falha ou fica cara | `MockLLM` já cobre a demo; o motor não depende de IA |
| Piloto não consegue 5 pessoas | Reportar o n real; incluir os próprios membros do time e pessoas que estudam |
| Conteúdo de Português com erro | Validação externa na quarta; revisão dupla de gabaritos |
| Demo cair no dia da avaliação | Vídeo bom, e README com como rodar local em 3 comandos |
| Tempo estourar | Cortar a prática; o diagnóstico + grafo + plano já sustentam o projeto |

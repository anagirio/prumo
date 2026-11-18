# Deploy do Prumo

O Prumo sobe como **um container só**: o Dockerfile compila o front e a API (FastAPI) serve o site e o `/api`. Resultado: um link único, sem CORS.

## Testar local com Docker (opcional)
```
make docker        # http://localhost:8000
```

## Opção A: Render (grátis, mais simples)
1. Crie conta em render.com com o GitHub.
2. New > Blueprint > escolha `anagirio/prumo` (ele lê o `render.yaml`).
3. Espere o build (uns 5 min). O link será `https://prumo-xxxx.onrender.com`.
4. Teste `/api/health` e faça um diagnóstico completo.

Avisos do plano grátis:
- Dorme após ~15 min sem acesso, e a primeira visita demora ~1 min. **Abra o link uns 2 min antes de gravar o vídeo e antes de qualquer avaliação.**
- O disco é temporário: o banco SQLite zera a cada deploy ou reinício. Para o demo está ok (cada aluno cria o próprio perfil na hora).

## Opção B: Fly.io ou Railway
Também aceitam o Dockerfile direto. Defina a porta pela variável `PORT` (já suportado).

## Variáveis de ambiente
| Variável | Para que serve | Padrão |
|---|---|---|
| `PORT` | porta do servidor | 8000 |
| `PRUMO_DB` | caminho do SQLite | /data/prumo.db |
| `PRUMO_STATIC` | pasta do front compilado | /app/static (no Docker) |
| `PRUMO_CORS` | origens extras, separadas por vírgula (só se o front ficar em outro domínio) | http://localhost:5173 |
| `PRUMO_LLM` | `mock` ou `anthropic` | mock |
| `ANTHROPIC_API_KEY` | chave, só com `PRUMO_LLM=anthropic` | vazio |

Se você hospedar o front separado (Vercel, Netlify), faça o build com `VITE_API_BASE=https://sua-api/api` e coloque o domínio do front em `PRUMO_CORS`.

## Cuidados
- **Nunca** commite a chave da API. Coloque só no painel do host.
- Chave com IA ligada gasta crédito a cada aula gerada. Para o júri, `mock` já mostra tudo; ligue a IA só se tiver orçamento e limite de gasto.
- Depois de 30/11 23:59 vale o code freeze: o deploy tem que estar estável antes.

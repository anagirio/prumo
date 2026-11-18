# Prumo em um container só: compila o front e serve tudo pela API (FastAPI).
# Build:  docker build -t prumo .
# Rodar:  docker run -p 8000:8000 -e PORT=8000 prumo   ->  http://localhost:8000

FROM node:20-slim AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY apps/api/pyproject.toml ./
COPY apps/api/prumo ./prumo
RUN pip install --no-cache-dir ".[llm]"
COPY --from=web /web/dist ./static

ENV PRUMO_STATIC=/app/static \
    PRUMO_DB=/data/prumo.db \
    PORT=8000
RUN mkdir -p /data
EXPOSE 8000
CMD ["sh", "-c", "uvicorn prumo.main:create_app --factory --host 0.0.0.0 --port ${PORT}"]

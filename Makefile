.PHONY: api-install web-install api web test simulate calibrate lint format build

api-install:
	cd apps/api && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

web-install:
	cd apps/web && npm install

api:
	cd apps/api && .venv/bin/uvicorn prumo.main:create_app --factory --reload --port 8000

web:
	cd apps/web && npm run dev

test:
	cd apps/api && .venv/bin/pytest -q

calibrate:
	cd apps/api && PYTHONPATH=. .venv/bin/python scripts/calibrate.py --out ../../docs/calibration_result.json

simulate:
	cd apps/api && .venv/bin/python scripts/simulate_students.py --students 500 --max-questions 12

lint:
	cd apps/api && .venv/bin/ruff check . && .venv/bin/ruff format --check .

format:
	cd apps/api && .venv/bin/ruff check . --fix && .venv/bin/ruff format .

build:
	cd apps/web && npm run build

docker:
	docker build -t prumo . && docker run --rm -p 8000:8000 prumo

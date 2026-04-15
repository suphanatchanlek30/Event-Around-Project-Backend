run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	python -m pytest -ra -W default

lint:
	ruff check app tests alembic/env.py
	black --check app tests alembic/env.py

format:
	ruff check app tests alembic/env.py --fix
	black app tests alembic/env.py

seed:
	python -m app.seed.seed_data
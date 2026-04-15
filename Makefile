PYTHON := $(shell if [ -x .venv/Scripts/python.exe ]; then echo .venv/Scripts/python.exe; elif [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python; fi)

run:
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PYTHON) -m pytest -ra -W default

lint:
	ruff check app tests alembic/env.py
	black --check app tests alembic/env.py

format:
	ruff check app tests alembic/env.py --fix
	black app tests alembic/env.py

seed:
	$(PYTHON) -m app.seed.seed_data
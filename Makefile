run:
	uvicorn app.main:app --reload

test:
	python -m pytest

seed:
	python -m app.seed.seed_data
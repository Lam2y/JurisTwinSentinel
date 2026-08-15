.PHONY: setup run test preflight docker-up docker-down verify

setup:
	python -m pip install -r backend/requirements.txt

run:
	cd backend && python run.py

test:
	cd backend && pytest -q

preflight:
	cd backend && python scripts/industry_preflight.py

verify:
	python -m compileall -q backend/app backend/scripts
	node --check backend/app/static/sentinel.js
	cd backend && pytest -q

docker-up:
	docker compose up --build

docker-down:
	docker compose down

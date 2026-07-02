.PHONY: build up down doctor optimize test shell clean stats report containers-clean

build:
	docker compose build

up:
	docker compose --profile dev up app-dev

down:
	docker compose --profile dev down --remove-orphans

containers-clean:
	docker compose down --remove-orphans
	docker container prune -f --filter label=com.docker.compose.project=pauper-cube

doctor:
	docker compose run --rm app doctor

optimize:
	docker compose run --rm app optimize data/input/cube.txt

test:
	docker compose run --rm app pytest --cov=cube_budget --cov-report=term-missing

shell:
	docker compose run --rm app bash

clean:
	docker compose run --rm app clean --all

stats:
	docker compose run --rm app stats

report:
	docker compose run --rm app report

update-cache:
	docker compose run --rm app update-cache data/input/cube.txt

prod-build:
	docker build -f docker/Dockerfile.prod -t cube-budget-optimizer:latest .

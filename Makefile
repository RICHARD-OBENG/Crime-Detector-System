.PHONY: help install install-dev build up down logs clean test lint format type-check run migrate

help:
	@echo "Crime Detector System - Development Commands"
	@echo "=============================================="
	@echo "make install          - Install production dependencies"
	@echo "make install-dev      - Install development dependencies"
	@echo "make build            - Build Docker images"
	@echo "make up               - Start development environment"
	@echo "make down             - Stop development environment"
	@echo "make logs             - View application logs"
	@echo "make clean            - Clean build artifacts and cache"
	@echo "make test             - Run tests with coverage"
	@echo "make lint             - Run code linter (ruff)"
	@echo "make format           - Format code with black"
	@echo "make type-check       - Run type checking with mypy"
	@echo "make run              - Run application locally"
	@echo "make migrate          - Run database migrations"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started. API available at http://localhost:8000"

down:
	docker-compose down

logs:
	docker-compose logs -f api

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

test:
	pytest

lint:
	ruff check src tests

format:
	black src tests

type-check:
	mypy src

run:
	uvicorn src.main:app --reload

migrate:
	alembic upgrade head

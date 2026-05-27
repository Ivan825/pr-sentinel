# PRSentinel

**PRSentinel** is a Pull Request Risk Intelligence Platform that analyzes GitHub pull requests before merge, detects risky changes, recommends targeted tests, and generates explainable reviewer reports using deterministic static analysis with optional AI-assisted summaries.

## What it does

PRSentinel helps reviewers answer:

- What changed in this PR?
- How risky is the change?
- Did it affect auth, APIs, database, config, dependencies, or tests?
- Are there security-sensitive changes?
- Are matching tests missing?
- Which tests should run?
- What should reviewers focus on first?

## Core capabilities

- GitHub PR diff ingestion
- Structured diff parsing
- File and change classification
- Static analysis rules
- API contract change detection
- Security-sensitive change detection
- Dependency and config risk detection
- Selective test recommendation
- Explainable risk scoring
- Markdown, JSON, and SARIF reports
- GitHub PR comments
- FastAPI backend
- CLI interface

## Tech stack

- Python
- FastAPI
- Typer
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- GitHub REST API
- tree-sitter
- pytest
- ruff
- mypy

## Local setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d
alembic upgrade head
Run API
uvicorn apps.api.main:app --reload
Run CLI
pr-sentinel doctor
pr-sentinel version

---

# Step 17: Run quality checks

Run:

```bash
ruff check .

Then:

mypy .

Then:

pytest

At this point, pytest will say no tests ran. That is okay for this step.
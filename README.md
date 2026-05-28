# PRSentinel — Pull Request Risk Intelligence Platform

PRSentinel is a production-style GitHub App that analyzes pull requests before they are merged. It combines deterministic static-analysis rules with bounded LLM-based semantic review to detect risky changes, compute explainable PR risk scores, recommend targeted tests, post/update GitHub PR comments, persist analysis history to PostgreSQL, expose FastAPI endpoints, and export SARIF reports for code-scanning workflows.

The project is designed as an SDE-focused developer-platform system, not a simple AI wrapper. The LLM is used only after deterministic context building, and every AI finding is normalized, validated, evidence-checked, confidence-filtered, and bounded before it can affect the final score.

---

## Demo

A demo pull request changes an `AuthFilter` implementation so that `isAllowed()` unconditionally returns `true`. PRSentinel flags this as a potential authentication bypass, recommends matching tests, computes a medium risk score, saves the analysis, and posts a GitHub App comment on the PR.

![PRSentinel GitHub App comment](docs/assets/github-app-comment.png)

Sample generated outputs are available in:

```text
docs/demo/sample-report.md
docs/demo/sample-report.json
docs/demo/sample-report.sarif
```

---

## What PRSentinel does

PRSentinel watches pull request events through a GitHub App webhook. When a PR is opened, reopened, synchronized, or marked ready for review, it fetches the PR metadata and changed files using a GitHub App installation token. It then parses diffs, classifies changed files, runs deterministic rules, recommends targeted tests, computes a base risk score, optionally runs a bounded LLM semantic reviewer, merges validated findings, persists the result to PostgreSQL, and posts/updates a PR comment.

The result is a practical risk-intelligence layer for code review. Instead of only saying “AI reviewed this PR,” PRSentinel gives structured evidence: which file changed, which rule fired, why the change is risky, what evidence supports it, what tests should be added, and how much the risk score changed.

---

## Key features

### Hybrid PR analysis

PRSentinel uses both deterministic and AI-assisted analysis. Deterministic rules handle stable patterns such as risky source changes without matching tests. The LLM layer handles semantic risk that simple rules may miss, such as an authorization method being changed to always allow access.

### Evidence-bounded LLM review

The LLM does not review the whole repository blindly. It receives a structured context packet containing selected changed lines, deterministic findings, file categories, test recommendations, and risk score context. Its output must match a strict JSON schema and pass validation before being accepted.

The semantic reviewer rejects low-confidence findings, invalid categories, invalid severities, duplicate missing-test findings, unsupported file paths, unsupported line numbers, and weak findings such as random comments being treated as secrets.

### Explainable risk scoring

PRSentinel computes a deterministic base score and then applies a bounded AI adjustment. The final report includes the total score, risk band, deterministic score, AI adjustment, and category-level breakdown.

Example:

```text
Overall Risk: MEDIUM — 39/100
Deterministic Score: 29/100
AI Adjustment: 10
Risk Breakdown: AUTH +17, TEST +12
```

### Targeted test recommendations

When risky source files change without matching tests, PRSentinel suggests likely unit/integration test files. This turns the report into an actionable review artifact instead of just a warning list.

### GitHub App integration

PRSentinel runs as a GitHub App. The app receives pull request webhook events, authenticates using a private key, creates short-lived installation tokens, fetches PR data, and posts comments as the GitHub App bot rather than a personal access token identity.

### Report formats

PRSentinel supports multiple output formats:

```text
Console report
Markdown PR comment
JSON structured report
SARIF static-analysis report
```

SARIF export makes the project compatible with code-scanning style workflows and gives the analyzer a standard machine-readable output format.

### Persistence and APIs

Every analysis can be saved to PostgreSQL. FastAPI endpoints expose saved analyses, repository-specific analysis history, and analysis detail records. This makes PRSentinel a platform backend rather than a one-off CLI script.

---

## Architecture

```text
GitHub Pull Request Event
        |
        v
GitHub App Webhook
        |
        v
FastAPI Backend
        |
        +--> Verify webhook signature
        |
        +--> Create GitHub App installation token
        |
        +--> Fetch PR metadata and changed files
        |
        +--> Parse unified diff hunks
        |
        +--> Detect language and classify file categories
        |
        +--> Run deterministic rule engine
        |
        +--> Generate targeted test recommendations
        |
        +--> Compute deterministic risk score
        |
        +--> Build bounded LLM context packet
        |
        +--> Run Groq LLM semantic reviewer
        |
        +--> Normalize and validate AI findings
        |
        +--> Apply bounded AI score adjustment
        |
        +--> Persist result to PostgreSQL
        |
        +--> Post/update GitHub PR comment
        |
        +--> Export Markdown / JSON / SARIF
```

---

## Tech stack

```text
Language: Python 3.11
API: FastAPI
CLI: Typer + Rich
Database: PostgreSQL
ORM/Migrations: SQLAlchemy + Alembic
GitHub Integration: GitHub REST API + GitHub App installation tokens
LLM Provider: Groq / Llama model
Validation: Pydantic
Reports: Markdown, JSON, SARIF
Quality: Pytest, Ruff, mypy
Deployment: Docker, Render, Neon PostgreSQL
```

---

## Repository structure

```text
apps/
  api/
    main.py
    routes/
      analysis.py
      analyses.py
      github_webhook.py
  cli/
    main.py

pr_sentinel/
  classifier/
  core/
  diff/
  engine/
  github/
  llm/
  reports/
  risk/
  rules/
  storage/
  testsuggester/

migrations/
tests/
docs/demo/
docs/assets/
scripts/
```

---

## Local setup

Clone the repository:

```bash
git clone https://github.com/Ivan825/pr-sentinel.git
cd pr-sentinel
```

Create and activate a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

Create environment file:

```bash
cp .env.example .env
```

Start local PostgreSQL:

```bash
docker compose up -d postgres
```

Run migrations:

```bash
alembic upgrade head
```

Run checks:

```bash
pytest && ruff check . && mypy .
```

---

## Environment variables

For local token-based development:

```env
APP_NAME=PRSentinel
APP_ENV=development
APP_DEBUG=true

DATABASE_URL=postgresql+psycopg2://prsentinel:prsentinel@localhost:5432/prsentinel

GITHUB_AUTH_MODE=token
GITHUB_TOKEN=your_github_token

LLM_PROVIDER=disabled
LLM_API_KEY=
LLM_MODEL=llama-3.1-8b-instant
LLM_MAX_FINDINGS=5
```

For GitHub App mode:

```env
GITHUB_AUTH_MODE=app
GITHUB_APP_ID=your_app_id
GITHUB_APP_PRIVATE_KEY_PATH=/path/to/private-key.pem
GITHUB_APP_PRIVATE_KEY_BASE64=
GITHUB_WEBHOOK_SECRET=your_webhook_secret
```

For production deployment, prefer `GITHUB_APP_PRIVATE_KEY_BASE64` instead of uploading a `.pem` file.

Generate the base64 private key value:

```bash
python scripts/encode_github_app_key.py /path/to/private-key.pem
```

Never commit `.env`, `.env.production`, `.pem`, `.key`, or private-key files.

---

## CLI usage

Fetch PR metadata:

```bash
pr-sentinel fetch-pr --repo Ivan825/prsentinel-demo --pr 7
```

Analyze PR in console:

```bash
pr-sentinel analyze-pr --repo Ivan825/prsentinel-demo --pr 7 --use-llm
```

Post/update a GitHub PR comment:

```bash
pr-sentinel analyze-pr \
  --repo Ivan825/prsentinel-demo \
  --pr 7 \
  --use-llm \
  --post-comment
```

Save analysis to PostgreSQL:

```bash
pr-sentinel analyze-pr \
  --repo Ivan825/prsentinel-demo \
  --pr 7 \
  --use-llm \
  --save
```

Generate Markdown report:

```bash
pr-sentinel analyze-pr \
  --repo Ivan825/prsentinel-demo \
  --pr 7 \
  --use-llm \
  --format markdown \
  --out docs/demo/sample-report.md
```

Generate JSON report:

```bash
pr-sentinel analyze-pr \
  --repo Ivan825/prsentinel-demo \
  --pr 7 \
  --use-llm \
  --format json \
  --out docs/demo/sample-report.json
```

Generate SARIF report:

```bash
pr-sentinel analyze-pr \
  --repo Ivan825/prsentinel-demo \
  --pr 7 \
  --use-llm \
  --format sarif \
  --out docs/demo/sample-report.sarif
```

List saved analyses:

```bash
pr-sentinel list-analyses
```

Filter saved analyses by repository:

```bash
pr-sentinel list-analyses --repo Ivan825/prsentinel-demo
```

---

## API usage

Run FastAPI locally:

```bash
uvicorn apps.api.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Analyze a PR:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "Ivan825/prsentinel-demo",
    "pr": 7,
    "use_llm": true,
    "post_comment": false,
    "save": true
  }'
```

List recent analyses:

```bash
curl http://127.0.0.1:8000/api/analyses
```

Get one saved analysis:

```bash
curl http://127.0.0.1:8000/api/analyses/1
```

List analyses for a repository:

```bash
curl http://127.0.0.1:8000/api/repositories/Ivan825/prsentinel-demo/analyses
```

GitHub webhook endpoint:

```text
POST /api/github/webhook?use_llm=true&post_comment=true&save=true
```

---

## GitHub App setup

Create a GitHub App from:

```text
GitHub → Settings → Developer settings → GitHub Apps → New GitHub App
```

Recommended repository permissions:

```text
Contents: Read-only
Metadata: Read-only
Pull requests: Read and write
Issues: Read and write
```

Subscribe to events:

```text
Pull request
```

Webhook URL:

```text
https://your-deployed-url/api/github/webhook?use_llm=true&post_comment=true&save=true
```

Install the app on the selected repository, such as:

```text
Ivan825/prsentinel-demo
```

After installation, PRSentinel will receive pull request events, analyze the PR, save the result, and post/update a PR comment as the GitHub App bot.

---

## Deployment

The deployed demo uses:

```text
Backend: Render Docker web service
Database: Neon PostgreSQL
LLM: Groq API
GitHub Integration: GitHub App
```

The Dockerfile runs migrations and starts Gunicorn with Uvicorn workers:

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && gunicorn apps.api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
```

Production environment variables are stored in the hosting provider, not committed to the repository.

A production `DATABASE_URL` should look like:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST/neondb?sslmode=require&channel_binding=require
```

Render free services may sleep when inactive, so for a live demo it is useful to open `/health` once before triggering a webhook.

---

## SARIF export

PRSentinel can export SARIF 2.1.0:

```bash
pr-sentinel analyze-pr \
  --repo Ivan825/prsentinel-demo \
  --pr 7 \
  --use-llm \
  --format sarif \
  --out docs/demo/sample-report.sarif
```

This allows PRSentinel findings to be represented in a standard static-analysis format with `ruleId`, severity level, message, artifact location, and custom properties.

---

## Design decisions

### Why deterministic rules and LLM together?

Deterministic rules are stable, cheap, and explainable. They work well for patterns like changed auth files, config risk, dependency changes, missing tests, and suspicious secrets. LLMs are better for semantic meaning, such as understanding that `return true` inside an authorization method may be an authentication bypass.

PRSentinel uses both, but the deterministic layer remains the foundation.

### Why bounded AI scoring?

The LLM cannot arbitrarily decide the final score. It can only add a bounded adjustment after producing validated, evidence-backed findings. This keeps the system explainable and prevents the AI layer from dominating the analysis.

### Why GitHub App instead of only a personal token?

A personal token is acceptable for local development, but a GitHub App is closer to a real developer-platform product. It supports installation-scoped permissions, short-lived installation tokens, bot identity comments, and repository-level installation control.

### Why SARIF?

SARIF is a standard format for static-analysis results. Exporting SARIF makes PRSentinel more interoperable with code-scanning and security workflows.

---

## Current limitations

PRSentinel is a project-scale implementation, not a full commercial code-review product. Current limitations include:

```text
No full repository-wide semantic indexing yet
No multi-tenant dashboard frontend yet
No queue/worker layer for very large PRs yet
No advanced policy-as-code rule configuration yet
LLM quality depends on provider/model behavior
```

These are intentional tradeoffs to keep the system focused and explainable.

---

## Future improvements

Possible next steps:

```text
Add a React dashboard for saved analyses
Add queue-based async processing with Redis/Celery
Add repository policy configuration
Add CODEOWNERS-aware review routing
Add GitHub Checks API annotations
Add SARIF upload into GitHub Code Scanning
Add richer test-impact analysis using dependency graphs
Add symbol-aware code indexing for deeper semantic review
```

---



## Status

PRSentinel currently supports:

```text
GitHub App webhook analysis
Deterministic rule engine
LLM semantic reviewer
Risk scoring
Test recommendations
Markdown, JSON, SARIF output
PostgreSQL persistence
FastAPI APIs
Docker deployment
CI quality checks
```


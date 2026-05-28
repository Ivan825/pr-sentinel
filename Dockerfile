FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY README.md ./README.md

COPY apps ./apps
COPY pr_sentinel ./pr_sentinel
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini

RUN pip install --upgrade pip \
    && pip install -e .

EXPOSE 8000

CMD ["gunicorn", "apps.api.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
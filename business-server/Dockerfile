# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY app/       ./app/
COPY server.py  ./
COPY config.json ./

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["python", "server.py"]

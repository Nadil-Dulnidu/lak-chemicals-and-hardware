# ── Stage 1: builder ──────────────────────────────────────────────────────────
# Install dependencies using uv into an isolated location so the final image
# only contains what is needed to run the app.
FROM python:3.11-slim AS builder

# Install uv (fast Python package manager used by this project)
RUN pip install uv

WORKDIR /app

# Copy dependency manifests first (better layer caching – deps rebuild only
# when pyproject.toml / uv.lock actually change)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies into /app/.venv so we can copy just that folder later
RUN uv sync --frozen --no-dev

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy the pre-built virtual env from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY app/       ./app/
COPY server.py  ./
COPY config.json ./

# Make the venv's binaries available without an explicit `source activate`
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port the gateway listens on (must match config.json → server.port)
EXPOSE 8002

# Run the server.  We override host/reload so it's safe inside a container:
#   • 0.0.0.0 → accept connections from outside the container
#   • --no-reload → file-watching / reloader is useless (and broken) in Docker
CMD ["python", "server.py"]

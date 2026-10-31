FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy uv binary (optional)
COPY --from=builder /uv /uvx /bin/
# Copy virtual environment
COPY --from=builder /app/.venv .venv

# Copy application code
COPY app/ app/
COPY alembic.ini migrations/ ./
COPY pyproject.toml ./
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Activate venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
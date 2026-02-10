FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system -e .

# Copy source code
COPY src/ ./src/
COPY entrypoint.sh ./

# Copy frontend build if exists
COPY static/ ./static/ 2>/dev/null || true

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create data directory
RUN mkdir -p /data

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

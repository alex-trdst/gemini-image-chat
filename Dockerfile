# Frontend build stage
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Build frontend (outputs to ../static which is /app/static)
COPY frontend/ ./
RUN npm run build

# Backend stage
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies
RUN uv pip install --system -e .

# Copy source code
COPY src/ ./src/
COPY entrypoint.sh ./

# Copy frontend build from builder stage (vite outputs to /app/static)
COPY --from=frontend-builder /app/static ./static/

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create data directory
RUN mkdir -p /data

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

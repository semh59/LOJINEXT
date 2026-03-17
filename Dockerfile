# Backend Dockerfile - Multi-stage Build
# ============================================================
# Builder Stage
FROM python:3.10-slim AS builder

ARG INSTALL_DEV=false

WORKDIR /app

# Install system dependencies needed for building requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY app/requirements.txt ./
COPY app/requirements-dev.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt && \
    if [ "$INSTALL_DEV" = "true" ]; then \
      pip install --no-cache-dir --prefix=/install -r requirements-dev.txt; \
    fi

# ============================================================
# Final Stage
FROM python:3.10-slim

ARG INSTALL_DEV=false

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    libgomp1 \
    postgresql-client \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app /app/app

# Copy alembic for database migrations
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create data directory with proper permissions
RUN mkdir -p /app/app/data /app/models /app/logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application via entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

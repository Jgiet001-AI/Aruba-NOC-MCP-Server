FROM python:3.11-slim

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for layer caching)
COPY requirements.txt .

# Install dependencies with uv (including test dependencies)
RUN uv pip install --system --no-cache -r requirements.txt && \
    uv pip install --system --no-cache pytest pytest-asyncio pytest-cov

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.server import app; print('OK')" || exit 1

# Use proper entrypoint - can be overridden by docker exec
ENTRYPOINT ["python", "-m", "src.server"]
CMD []

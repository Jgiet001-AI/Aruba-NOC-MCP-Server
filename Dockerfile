FROM python:3.11-slim

# Upgrade pip to fix MEDIUM vulnerability
RUN pip install --no-cache-dir --upgrade pip

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Create non-root user BEFORE copying files
RUN groupadd -r mcp && \
    useradd -r -g mcp -u 1000 -m -s /bin/bash mcp

# Set working directory
WORKDIR /app

# Copy dependency files first (for layer caching)
COPY --chown=mcp:mcp requirements.txt .

# Install dependencies with uv (including test dependencies)
RUN uv pip install --system --no-cache -r requirements.txt && \
    uv pip install --system --no-cache pytest pytest-asyncio pytest-cov

# Copy source code with correct ownership
COPY --chown=mcp:mcp src/ ./src/

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER mcp

# Run the MCP server
# Note: Container stays alive; MCP client invokes server via: docker exec -i <container> python -m src.server
CMD ["tail", "-f", "/dev/null"]

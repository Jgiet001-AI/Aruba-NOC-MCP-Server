FROM python:3.11-slim

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files first (for layer caching)
COPY requirements.txt .

# Install dependencies with uv
RUN uv pip install --system --no-cache -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the MCP server
# Note: Container stays alive; MCP client invokes server via: docker exec -i <container> python -m src.server
CMD ["tail", "-f", "/dev/null"]

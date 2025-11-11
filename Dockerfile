FROM python:3.11-slim

# Build argument for install profile (full, api-cloud, etc.)
ARG INSTALL_PROFILE=full

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH (installed to /root/.local/bin)
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Install dependencies based on profile
# - full: All features (torch, sentence-transformers, etc.) - 3GB image
# - api-cloud: Cloud-optimized (no torch, use OpenAI API) - 1GB image
RUN if [ "$INSTALL_PROFILE" = "api-cloud" ]; then \
        echo "Installing cloud-optimized dependencies (no torch)..."; \
        /root/.local/bin/uv sync --extra api-cloud --extra auth --extra mcp; \
    else \
        echo "Installing all dependencies..."; \
        /root/.local/bin/uv sync --all-extras; \
    fi

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Default command (can be overridden in docker-compose.yml)
CMD ["uv", "run", "uvicorn", "kagura.api.server:app", "--host", "0.0.0.0", "--port", "8080"]

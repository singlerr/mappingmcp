# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_SYSTEM_PYTHON=1

# Transport configuration (stdio, sse, streamable-http)
ENV MCP_TRANSPORT=stdio
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080

# Install uv for package management
RUN pip install --no-cache-dir uv

# Create app directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system -e .

# Create cache directory for mappings
RUN mkdir -p /root/.cache/mappingmcp

# Expose port for HTTP-based transports
EXPOSE 8080

# Health check for HTTP transports
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD if [ "$MCP_TRANSPORT" != "stdio" ]; then curl -f http://localhost:${MCP_PORT}/health || exit 1; else exit 0; fi

# Run the server
ENTRYPOINT ["python", "-m", "mappingmcp"]

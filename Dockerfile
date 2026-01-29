# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_SYSTEM_PYTHON=1

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

# The MCP server uses stdio transport by default
# Run the server
ENTRYPOINT ["python", "-m", "mappingmcp"]

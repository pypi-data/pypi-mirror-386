# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy the entire project first for installation
COPY . .

# Install the package and its dependencies
RUN uv pip install --system --no-cache-dir -e .

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=8000

# Run the application
CMD ["rootly-mcp-server", "--transport", "sse", "--log-level", "INFO", "--hosted"]

FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PDF processing
    poppler-utils \
    # For building some Python packages
    build-essential \
    # curl for healthcheck
    curl \
    vim \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
# UID/GID default to 1000 to match typical host users; override at build time if needed
ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} chatbot && useradd -u ${UID} -g chatbot -d /app -m chatbot

# Set working directory
WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=chatbot:chatbot . .

# Create necessary directories
RUN mkdir -p /app/logs /app/documents && \
    chown -R chatbot:chatbot /app

# Switch to non-root user
USER chatbot

# Expose port
EXPOSE 8000

# Default command (can be overridden in compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]

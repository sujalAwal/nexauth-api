# Stage 1: Builder - Download dependencies and prepare environment
# We use Python 3.12 slim image for smaller image size
FROM python:3.12-slim as builder

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required for building Python packages
# - build-essential: compiler tools
# - unixodbc-dev: required for pyodbc to connect to MSSQL
# - gnupg: for package verification
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gnupg \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Lean production image with only what's needed
FROM python:3.12-slim

# Set environment variables
# PYTHONUNBUFFERED=1: Ensures Python output is logged immediately (important for Docker logs)
# PATH: Include venv bin in PATH so Python packages work without activation
ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

# Install runtime dependencies only (smaller than builder)
# Including Microsoft ODBC drivers for SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    unixodbc \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft's package repository and install ODBC driver 18
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg && \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder stage (faster than pip installing again)
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Health check - Docker will check if app is responsive every 10 seconds
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port 8000 where FastAPI will run
EXPOSE 8000

# Run the application using Uvicorn
# - host 0.0.0.0: Accept connections from any interface (required for Docker)
# - port 8000: Port to run on
# - workers: Number of worker processes (adjust based on CPU cores)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

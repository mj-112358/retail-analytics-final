# PRODUCTION DOCKERFILE - SQLALCHEMY VERSION
# Complete retail analytics with PostgreSQL and SQLAlchemy ORM

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies optimized for DigitalOcean
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy SQLAlchemy requirements
COPY requirements.sqlalchemy.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy SQLAlchemy application files
COPY main_sqlalchemy.py main.py
COPY database.py .
COPY models.py .
COPY create_tables.py .
COPY test_connection.py .

# Create logs directory
RUN mkdir -p /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose port
EXPOSE 8080

# Start command
CMD ["sh", "-c", "python main.py --port ${PORT:-8080} --host 0.0.0.0"]
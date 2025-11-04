# Python Dockerfile Template
# For Python web apps, APIs, scripts, etc.

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Expose port (adjust as needed)
EXPOSE 8000

# For Flask app - use gunicorn for production or flask run for dev
# Production (recommended):
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]

# Development (if you want hot reload):
# CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]

# Or use the app's built-in server:
# CMD ["python", "app.py"]

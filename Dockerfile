# Use Python 3.9 as the base image (compatible with your requirements)
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to ensure we get binaries
RUN pip install --no-cache-dir --upgrade pip

# Copy core requirements first (cache hit likely)
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# Copy ML requirements (heavy, changed less often)
COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt
RUN pip install matplotlib

# Copy the rest of the application
COPY . .

# Expose port 7860 for Hugging Face Spaces
EXPOSE 7860
ENV APP_PORT=7860
ENV PYTHONUNBUFFERED=1

# Fix permissions for Hugging Face (which runs as non-root user 1000)
# Create necessary directories and make everything writable
RUN mkdir -p /app/static/uploads && \
    chmod -R 777 /app

# Command to run the application
CMD ["python", "app_main.py"]
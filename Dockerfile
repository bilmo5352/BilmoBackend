# Dockerfile for BilmoBackend (single-stage, no multi-stage)

# Use a slim Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including Chrome for Selenium)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc \
    wget \
    gnupg \
    curl \
    ca-certificates \
    xdg-utils \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
 && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get install -y --no-install-recommends /tmp/chrome.deb \
 && rm /tmp/chrome.deb \
 && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Install requests explicitly (ensures healthcheck works)
RUN pip install --no-cache-dir requests

# Create necessary directories
RUN mkdir -p html_files logs templates static \
 && chmod 755 html_files logs

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=smart_api.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1

# Create a non-root user for security
RUN useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app
USER appuser

# Expose the Flask port
EXPOSE 5000

# Healthcheck using Python (requests must be in requirements.txt)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD ["python", "-c", "import requests,sys; r=requests.get('http://localhost:5000/status'); sys.exit(0 if r.status_code==200 else 1)"]

# Command to run the Smart API
CMD ["python", "smart_api.py"]

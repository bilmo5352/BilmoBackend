# Fixed multi-stage Dockerfile for BilmoBackend

# ────────────────
# Builder stage: install Python deps
# ────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc \
 && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies globally
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ────────────────
# Production stage: install runtime deps + copy code
# ────────────────
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies including Chrome for Selenium
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    wget gnupg curl ca-certificates xdg-utils \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libxss1 libxtst6 \
 && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get install -y --no-install-recommends /tmp/chrome.deb \
 && rm /tmp/chrome.deb \
 && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p html_files logs templates static \
 && chmod 755 html_files logs

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=smart_api.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app
USER appuser

# Expose Flask port
EXPOSE 5000

# Health check via Python requests
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python - << 'EOF'
import requests, sys
r = requests.get("http://localhost:5000/status")
sys.exit(0 if r.status_code==200 else 1)
EOF

# Run the Smart API
CMD ["python", "smart_api.py"]

# 🐧 Base image with Python
FROM python:3.10-slim

# 🛠️ Install system dependencies including Chrome and chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libxss1 \
    libappindicator3-1 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libasound2 \
    libxrandr2 \
    libu2f-udev \
    xdg-utils \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 🔐 Environment variables (optional defaults)
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV LOGIN_FILE=/data/LOGS.txt
ENV FAILED_LOGINS_FILE=/data/failed_logins.txt
ENV RETRY_LOG_DIR=/data/retry_logs

# 📁 Create working directory
WORKDIR /app

# 🐍 Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 📁 Copy your orchestration script
COPY mega_online_auto.py .

# 📁 Create data directory for logs
RUN mkdir -p /data/retry_logs

# 🚀 Entry point
CMD ["python", "mega_online_auto.py"]

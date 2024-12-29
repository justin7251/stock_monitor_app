FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including cron
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    cron \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


# Copy the rest of the application
COPY . .

# Setup cron job
COPY crontab /etc/cron.d/stock-updater
RUN chmod 0644 /etc/cron.d/stock-updater

# Create log files
RUN touch /var/log/price_updater.log && \
    touch /var/log/historical_data.log && \
    chmod 0666 /var/log/price_updater.log && \
    chmod 0666 /var/log/historical_data.log

# Install crontab
RUN crontab /etc/cron.d/stock-updater

# Create entrypoint script
RUN echo '#!/bin/bash\nservice cron start\nflask run --host=0.0.0.0' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Start cron and your application
CMD ["/entrypoint.sh"]

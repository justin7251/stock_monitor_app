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

# Install cron and setup environment
RUN apt-get update && apt-get install -y cron

# Setup environment variables for cron
RUN echo "SHELL=/bin/bash\n\
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n\
PYTHONPATH=/app\n\
\n\
# Update stock prices every 15 minutes during market hours (9:30 AM - 4:00 PM EST, Monday-Friday)\n\
*/15 9-16 * * 1-5 cd /app && python app/tasks/stock_updater.py >> /var/log/price_updater.log 2>&1\n\
\n\
# Run historical data update once per day after market close (5:00 PM EST, Monday-Friday)\n\
0 17 * * 1-5 cd /app && python app/tasks/stock_updater.py >> /var/log/historical_data.log 2>&1\n" > /etc/cron.d/stock-updater

# Set permissions for cron job
RUN chmod 0644 /etc/cron.d/stock-updater

# Create log files and set permissions
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

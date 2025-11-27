# Python Analytics Service Dockerfile
FROM python:3.11-slim

# Install necessary packages
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -g 1001 analytics && \
    useradd -u 1001 -g analytics -s /bin/bash -m analytics

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python scripts
COPY *.py ./
COPY run_analytics.sh ./

# Make the script executable
RUN chmod +x run_analytics.sh

# Change ownership to non-root user
RUN chown -R analytics:analytics /app

# Switch to non-root user
USER analytics

# Analytics service doesn't need to expose ports (scheduled background process)

# Run analytics every 6 hours (21600 seconds)
# Using exec to ensure proper signal handling
CMD ["sh", "-c", "while true; do ./run_analytics.sh; sleep 21600; done"]





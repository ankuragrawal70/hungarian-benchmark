FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for psutil
RUN apt-get update && apt-get install -y gcc python3-dev && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY main.py .

# Make script executable
RUN chmod +x main.py

# Create results directory
RUN mkdir -p /results

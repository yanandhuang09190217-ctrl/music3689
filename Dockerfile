FROM python:3.11-slim

# Install system deps and ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg build-essential libssl-dev libffi-dev curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app

# Install python deps
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    pip3 install -r requirements.txt

# Expose default web port for Render health checks (Render will set PORT env)
EXPOSE 10000

CMD ["python3", "main.py"]
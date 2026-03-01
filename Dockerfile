# Use Python 3.11 slim
FROM python:3.11-slim

# Install system dependencies for Piper
RUN apt-get update && apt-get install -y \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all files (including engine-python/ folder)
COPY . .

# Install requirements
RUN pip install --no-cache-dir fastapi uvicorn piper-tts python-multipart

# Cloud Run default port
EXPOSE 8080

# Command to run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
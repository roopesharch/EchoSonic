# 1. Use Python 3.11 slim (stable and small)
FROM python:3.11-slim

# 2. Prevent Python from buffering logs (Crucial for Cloud Run logs)
ENV PYTHONUNBUFFERED=1

# 3. Install system dependencies for Piper audio
RUN apt-get update && apt-get install -y \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 4. Copy and Install requirements FIRST (Better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the code (including engine-python folder)
COPY . .

# 6. Expose Port 8080
EXPOSE 8080

# 7. Start FastAPI with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
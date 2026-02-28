FROM python:3.9-slim

# 1. Install Go, Wget, and Audio Libraries
COPY --from=golang:1.21-bullseye /usr/local/go/ /usr/local/go/
ENV PATH="/usr/local/go/bin:${PATH}"
# libsndfile1 is critical for the python piper library to write WAVs
RUN apt-get update && apt-get install -y wget libasound2 libsndfile1 

WORKDIR /app
COPY . .

# 2. Build Go Gateway
RUN cd gateway-go && go build -o gateway main.go

# 3. Install Python dependencies (Cleaned up)
RUN pip install grpcio grpcio-tools piper-tts

# 4. (Optional) Download Piper binary 
# Note: Since we use 'import piper' in server.py now, we mainly need the .onnx models
RUN cd engine-python && \
    wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz && \
    tar -xf piper_amd64.tar.gz && \
    rm piper_amd64.tar.gz

# 5. CRITICAL: Permissions for the shared audio file
RUN touch /app/shared_output.wav && chmod 777 /app/shared_output.wav

EXPOSE 8080

# 6. Run both
CMD ["sh", "-c", "python3 engine-python/server.py & ./gateway-go/gateway"]
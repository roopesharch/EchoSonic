FROM python:3.9-slim

# Install Go, Wget, and Audio Libraries
COPY --from=golang:1.21-bullseye /usr/local/go/ /usr/local/go/
ENV PATH="/usr/local/go/bin:${PATH}"
RUN apt-get update && apt-get install -y wget libasound2

WORKDIR /app
COPY . .

# Build Go Gateway
RUN cd gateway-go && go build -o gateway main.go

# Install Python deps
RUN pip install grpcio grpcio-tools

# Download Piper binary for the cloud environment
RUN cd engine-python && \
    wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz && \
    tar -xf piper_amd64.tar.gz

EXPOSE 8080

# Run both Python and Go in parallel
CMD ["sh", "-c", "python3 engine-python/server.py & ./gateway-go/gateway"]
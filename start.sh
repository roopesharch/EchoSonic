#!/bin/bash

# 1. Start the Python AI Engine in the background
echo "🤖 Starting Python AI Engine..."
cd engine-python
# Run the server and save its process ID (PID)
python server.py &
PYTHON_PID=$!

# 2. Give the AI 3 seconds to load its models
echo "⏳ Waiting for models to initialize..."
sleep 3

# 3. Start the Go Gateway
echo "🌐 Starting Go Gateway..."
cd ../gateway-go
go run main.go &
GO_PID=$!

# 4. Handle Shutdown: If you press Ctrl+C, kill both processes cleanly
trap "kill $PYTHON_PID $GO_PID; echo -e '\n🛑 Stopping EchoSonic servers...'; exit" INT

# Keep the script running so you can see the logs
wait

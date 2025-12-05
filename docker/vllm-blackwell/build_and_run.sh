#!/bin/bash
# =================================================================================
# Quick build and test script for vLLM Blackwell Docker
# =================================================================================

set -e  # Exit on error

echo "========================================="
echo "vLLM Blackwell Docker Build & Test"
echo "========================================="
echo

# Change to script directory
cd "$(dirname "$0")"

# Check prerequisites
echo "[1/5] Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    exit 1
fi

if ! nvidia-smi &> /dev/null; then
    echo "ERROR: nvidia-smi not found. Is NVIDIA driver installed?"
    exit 1
fi

echo "✓ Docker: $(docker --version)"
echo "✓ Docker Compose: $(docker compose version 2>/dev/null || docker-compose --version)"
echo "✓ NVIDIA Driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
echo

# Copy .env if not exists
if [ ! -f .env ]; then
    echo "[2/5] Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
else
    echo "[2/5] .env file already exists"
fi
echo

# Build image
echo "[3/5] Building Docker image (this may take 20-30 minutes)..."
echo "Press Ctrl+C to cancel"
sleep 3

docker compose build

echo "✓ Image built successfully"
echo

# Start service
echo "[4/5] Starting vLLM service..."
docker compose up -d

echo "✓ Service started"
echo

# Wait for initialization
echo "[5/5] Waiting for service to be ready..."
echo "This may take 5-10 minutes for model loading..."

max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo
        echo "✓ Service is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo
    echo "ERROR: Service did not become ready in time"
    echo "Check logs with: docker compose logs"
    exit 1
fi

echo
echo "========================================="
echo "SUCCESS! vLLM is running"
echo "========================================="
echo
echo "API endpoint: http://localhost:8000"
echo "Health check: http://localhost:8000/health"
echo "Models: http://localhost:8000/v1/models"
echo
echo "View logs: docker compose logs -f"
echo "Stop service: docker compose down"
echo

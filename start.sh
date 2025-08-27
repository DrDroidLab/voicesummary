#!/bin/bash

# Voice Summary API Startup Script

echo "Starting Voice Summary API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy env.example to .env and configure your settings."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed!"
    echo "Please install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
uv sync

# Run database migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Start the application
echo "Starting the application..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

#!/bin/bash

# Pokemon Image Recognition App Setup Script

set -e

echo "🚀 Setting up Pokemon Image Recognition App..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.11+ and try again."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment and install dependencies
echo "📦 Creating virtual environment and installing dependencies..."
make install

echo "🐳 Setting up Docker environment..."
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker and Docker Compose found"
    echo "🔧 Building Docker containers..."
    make docker-build
    echo "✅ Docker setup complete"
else
    echo "⚠️  Docker or Docker Compose not found. You can still run the app locally."
    echo "   To use Docker, install Docker Desktop and run 'make docker-build'"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To get started:"
echo "  • Run locally: make dev"
echo "  • Run with Docker: make docker-up"
echo "  • Run tests: make test"
echo "  • View all commands: make help"
echo ""
echo "The API will be available at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
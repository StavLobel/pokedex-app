#!/bin/bash

# Activation helper script for Pokemon Image Recognition App

if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found. Run 'make install' first."
    exit 1
fi

echo "🐍 Activating virtual environment..."
echo "Run the following command:"
echo ""
echo "source backend/venv/bin/activate"
echo ""
echo "Or use the Makefile commands:"
echo "  make dev    # Run development server"
echo "  make test   # Run tests"
echo "  make lint   # Run linting"
echo "  make format # Format code"
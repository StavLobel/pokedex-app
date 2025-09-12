# Pokemon Image Recognition App

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.6+-red.svg)](https://pytorch.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)
[![Linting](https://img.shields.io/badge/Linting-Flake8-lightgrey.svg)](https://flake8.pycqa.org/)
[![Type Checking](https://img.shields.io/badge/Type%20Checking-MyPy-blue.svg)](https://mypy.readthedocs.io/)

<!-- Future badges to add during development:
[![Build Status](https://github.com/StavLobel/pokedex-app/workflows/CI/badge.svg)](https://github.com/StavLobel/pokedex-app/actions)
[![Coverage](https://codecov.io/gh/StavLobel/pokedex-app/branch/main/graph/badge.svg)](https://codecov.io/gh/StavLobel/pokedex-app)
[![Security](https://snyk.io/test/github/StavLobel/pokedex-app/badge.svg)](https://snyk.io/test/github/StavLobel/pokedex-app)
[![Dependencies](https://img.shields.io/badge/Dependencies-Up%20to%20Date-brightgreen.svg)](https://github.com/StavLobel/pokedex-app/network/dependencies)
[![API Docs](https://img.shields.io/badge/API-Docs-blue.svg)](https://stavlobel.github.io/pokedex-app/docs)
[![Demo](https://img.shields.io/badge/Demo-Live-success.svg)](https://pokedex-app.example.com)
[![Docker Pulls](https://img.shields.io/docker/pulls/stavlobel/pokedex-app.svg)](https://hub.docker.com/r/stavlobel/pokedex-app)
[![GitHub Release](https://img.shields.io/github/v/release/StavLobel/pokedex-app.svg)](https://github.com/StavLobel/pokedex-app/releases)
[![GitHub Issues](https://img.shields.io/github/issues/StavLobel/pokedex-app.svg)](https://github.com/StavLobel/pokedex-app/issues)
[![GitHub Stars](https://img.shields.io/github/stars/StavLobel/pokedex-app.svg)](https://github.com/StavLobel/pokedex-app/stargazers)
-->

A production-grade Pokédex web application that enables users to identify Pokémon through AI-powered image recognition.

## Features

- 📱 Mobile-first Progressive Web App (PWA)
- 🤖 AI-powered Pokemon identification
- 📊 Comprehensive Pokemon data from PokéAPI
- ⚡ Fast response times (<10 seconds for recognition)
- 🔄 Real-time camera capture and file upload
- 📈 Production-ready with monitoring and CI/CD

## Architecture

- **Frontend**: React with Lovable components, PWA capabilities
- **Backend**: FastAPI with async support
- **AI**: Pre-trained Pokemon classification model
- **Database**: PostgreSQL with Redis caching
- **Deployment**: Docker containers on Hostinger VPS with Traefik

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend development)

### Development Setup

#### Quick Setup (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd pokedex-app
```

2. Run the setup script:
```bash
./setup.sh
```

3. Start the development server:
```bash
make dev
```

4. The API will be available at `http://localhost:8000`
5. API documentation at `http://localhost:8000/docs`

#### Docker Setup

1. Start the development environment:
```bash
make docker-up
```

2. The API will be available at `http://localhost:8000`
3. API documentation at `http://localhost:8000/docs`

### Backend Development

1. Set up the virtual environment and install dependencies:
```bash
make install
```

2. Run the development server:
```bash
make dev
```

Alternatively, you can set up manually:

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the development server:
```bash
python run_dev.py
```

### Testing

Run the test suite:
```bash
make test
```

Run with coverage:
```bash
make test-cov
```

### Code Quality

Format code:
```bash
make format
```

Run linting:
```bash
make lint
```

## Project Structure

```
pokedex-app/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Core configuration
│   │   ├── models/            # Data models
│   │   ├── services/          # Business logic
│   │   └── main.py            # FastAPI app
│   ├── tests/
│   │   ├── unit/              # Unit tests
│   │   └── integration/       # Integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React frontend (to be created)
├── docker-compose.yml          # Development environment
├── .gitignore
└── README.md
```

## API Endpoints

- `POST /api/v1/identify` - Upload image for Pokemon identification
- `GET /api/v1/pokemon/{id}` - Get Pokemon data by ID
- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/models/status` - AI model status

## Environment Variables

Create a `.env` file in the backend directory:

```env
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres:password@localhost:5432/pokemon_db
REDIS_URL=redis://localhost:6379
POKEAPI_BASE_URL=https://pokeapi.co/api/v2
AI_MODEL_PATH=./models/pokemon_classifier.pkl
LOG_LEVEL=INFO
```

## Deployment

The application is designed for deployment on Hostinger VPS using Docker containers with Traefik as a reverse proxy.

### Production Deployment

1. Set up environment variables for production
2. Build and push Docker images
3. Deploy using Docker Compose with production configuration
4. Configure Traefik for SSL termination and load balancing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the coding standards
4. Write tests for new functionality
5. Submit a pull request

## Testing Strategy

- **Unit Tests**: 70% coverage target
- **Integration Tests**: API endpoint testing
- **End-to-End Tests**: Complete user journey testing
- **Performance Tests**: Response time validation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the GitHub repository.
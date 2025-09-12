# Pokemon Image Recognition App

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
# Voice Summary

A Pythonic project for managing audio call information with FastAPI, PostgreSQL, and S3 integration.

## Features

- FastAPI backend with async support
- PostgreSQL database for storing call information
- S3 integration for audio file storage
- RESTful API for managing audio calls
- Utility functions for accessing call data
- Docker-based deployment for easy setup
- Comprehensive client testing tools
- CLI tools for shell access and database operations

## Project Structure

```
voicesummary/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── calls.py
│   └── utils/
│       ├── __init__.py
│       ├── s3.py
│       └── call_utils.py
├── alembic/
│   └── versions/
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── env.example
├── env.production
├── deploy.sh
├── client_test.py
├── cli.py
├── shell.py
├── test_example.py
└── README.md
```

## Quick Start with Docker (Recommended)

### Prerequisites

- Docker and Docker Compose installed
- AWS S3 bucket and credentials

### One-Command Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd voicesummary
   ```

2. **Deploy with one command**
   ```bash
   ./deploy.sh
   ```

   The script will:
   - Create a `.env` file from template
   - Prompt you to configure AWS credentials
   - Build and start all services
   - Run database migrations
   - Verify service health

3. **Access your application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - pgAdmin: http://localhost:5050 (admin@voicesummary.com / admin123)

### Manual Docker Setup

If you prefer manual setup:

1. **Configure environment**
   ```bash
   cp env.production .env
   # Edit .env with your AWS credentials
   ```

2. **Start services**
   ```bash
   docker-compose up --build -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec app alembic upgrade head
   ```

## Traditional Setup (without Docker)

### Prerequisites

- Python 3.9+
- PostgreSQL
- AWS S3 bucket
- uv package manager

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```

3. Copy environment file and configure:
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

4. Set up PostgreSQL database:
   ```bash
   createdb voicesummary
   ```

5. Run database migrations:
   ```bash
   uv run alembic upgrade head
   ```

6. Start the application:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## Configuration

### Environment Variables

#### Required for S3 Access
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `S3_BUCKET_NAME`: Your S3 bucket name for audio files

#### Optional
- `AWS_REGION`: AWS region (default: us-east-1)
- `DEBUG`: Enable debug mode (default: false)

#### Database (Auto-configured in Docker)
- `DATABASE_URL`: PostgreSQL connection string (auto-set in Docker)

### Where to Put Credentials

1. **For Docker deployment**: Edit the `.env` file created by `deploy.sh`
2. **For local development**: Edit `env.example` and copy to `.env`
3. **For production**: Set environment variables directly on the server/container

## API Endpoints

- `POST /api/calls/` - Create a new call record
- `GET /api/calls/{call_id}` - Get call information by ID
- `GET /api/calls/{call_id}/audio` - Download audio file
- `GET /api/calls/{call_id}/transcript` - Get transcript JSON
- `GET /api/calls/` - List all calls with pagination
- `PUT /api/calls/{call_id}` - Update call records
- `DELETE /api/calls/{call_id}` - Delete call records

## Client Testing

### Comprehensive Testing Script

Use the included `client_test.py` script for testing:

```bash
# Basic health check
python client_test.py

# Run comprehensive tests with sample data
python client_test.py --create-sample-calls

# Test against different API URL
python client_test.py --base-url https://api.example.com

# Clean up test data
python client_test.py --cleanup

# Show help
python client_test.py --help
```

### Sample Call Data

The client script creates realistic sample calls with:
- Multiple participants
- Timestamped conversation
- Confidence scores
- Call metadata (duration, type, sentiment)
- S3 audio file URLs

## Shell Access and CLI Tools

### Command Line Interface (CLI)

Use `cli.py` for quick database operations from the shell:

```bash
# Get call information
python cli.py get-call call_001_20241201

# Get transcript
python cli.py get-transcript call_001_20241201

# Get presigned audio URL
python cli.py get-audio-url call_001_20241201

# List all calls
python cli.py list-calls --limit 5

# Create a new call
python cli.py create-call test_001 '{"participants": ["John"], "summary": "Test call"}' s3://bucket/test.mp3

# Validate audio file exists
python cli.py validate-audio s3://bucket/test.mp3

# Show help
python cli.py --help
```

### Interactive Python Shell

Use `shell.py` for interactive database exploration:

```bash
python shell.py
```

This provides an interactive Python shell with:
- Pre-loaded database session functions
- All utility functions available
- Database models and schemas imported
- Helpful examples and tips

### Direct Function Calls

If you want to call functions directly from Python:

```python
# Import what you need
from app.database import SessionLocal
from app.utils.call_utils import get_call_by_id

# Create a database session
db = SessionLocal()

try:
    # Use the function
    call = get_call_by_id("call_001", db)
    print(call)
finally:
    # Always close the session
    db.close()
```

## Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up --build -d

# Access app container
docker-compose exec app bash

# Run migrations
docker-compose exec app alembic upgrade head
```

## Development

- Format code: `uv run black .`
- Sort imports: `uv run isort .`
- Run tests: `uv run pytest`
- Or use Makefile: `make format`, `make lint`, `make test`

## Troubleshooting

### Common Issues

1. **S3 Access Denied**: Verify AWS credentials and bucket permissions
2. **Database Connection Failed**: Check PostgreSQL container status
3. **Port Already in Use**: Stop existing services or change ports in docker-compose.yml

### Logs and Debugging

```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs app
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f app
```

### Health Checks

- API Health: http://localhost:8000/health
- Database: `docker-compose exec postgres pg_isready`
- Container Status: `docker-compose ps`

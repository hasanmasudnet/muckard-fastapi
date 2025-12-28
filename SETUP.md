# FastAPI Backend Setup Guide

## Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- (Optional) HashiCorp Vault for production

## Step-by-Step Setup

### 1. Create Virtual Environment

```bash
cd fastapi-backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example file
cp env.example .env

# Edit .env with your actual values
```

**Required Variables:**

```env
APP_NAME=Muckard FastAPI Backend
DEBUG=True
API_V1_PREFIX=/api/v1

# Security
SECRET_KEY=  # Leave empty to auto-generate
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@localhost:5432/muckard_db

# Redis (REQUIRED)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Vault (Optional for development)
VAULT_URL=http://localhost:8200
VAULT_TOKEN=
VAULT_MOUNT_PATH=secret

# Kraken API
KRAKEN_API_BASE_URL=https://api.kraken.com

# CORS (REQUIRED)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,https://dev.muckard.com,https://admin.muckard.com
```

### 4. Set Up Database

```bash
# Create database (PostgreSQL)
createdb muckard_db

# Or using psql:
psql -U postgres
CREATE DATABASE muckard_db;
```

### 5. Run Database Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 6. Start Redis (if not running)

```bash
# Windows (if installed)
redis-server

# Linux/Mac
sudo systemctl start redis
# or
redis-server
```

### 7. Start the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 8. Verify Installation

- API Root: http://localhost:8000/
- Health Check: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing the API

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "Test1234!"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test1234!"
```

### 3. Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Development Workflow

### Creating New Migrations

```bash
# After model changes
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Running Tests (when implemented)

```bash
pytest
```

### Code Formatting

```bash
# Install black
pip install black

# Format code
black app/
```

## Troubleshooting

### Database Connection Error

- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Ensure database exists

### Redis Connection Error

- Verify Redis is running
- Check `REDIS_HOST` and `REDIS_PORT` in `.env`
- Test connection: `redis-cli ping`

### Vault Connection Error

- Vault is optional for development
- If not using Vault, Kraken key storage will fail
- For development, you can modify `kraken_service.py` to skip Vault

### Import Errors

- Ensure virtual environment is activated
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python path includes `fastapi-backend` directory

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Use strong `SECRET_KEY` (not auto-generated)
3. Configure proper `CORS_ORIGINS`
4. Set up HashiCorp Vault
5. Use environment-specific database
6. Configure reverse proxy (nginx)
7. Set up SSL/TLS certificates
8. Configure logging and monitoring

## Next Steps

- Implement remaining admin endpoints
- Add notification service
- Add support ticket service
- Set up comprehensive testing
- Configure EFK stack for observability
- Add rate limiting
- Implement API versioning strategy

# Muckard Trading Platform - Microservices Backend

FastAPI microservices backend for the Muckard trading platform, serving both `dev.muckard.com` and `admin.muckard.com` frontends.

## Architecture

This project uses a **microservices architecture** with the following services:

- **User Service** (Port 8000): Authentication, user management, onboarding
- **Kraken Service** (Port 8001): Kraken API integration, trading data, bot status
- **Bot Service** (Port 8002): Trading bot execution (in `muckai/muckai/`)

All services share:
- PostgreSQL database (shared)
- Redis cache
- Kafka (event streaming)
- RabbitMQ (commands & real-time notifications)

## Quick Start

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Copy the example file
cp env.example .env

# Edit .env and fill in ALL required values
# All fields are required - no defaults in code
```

4. **Run database migrations (centralized)**
```bash
# Migrations import models from all services
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

5. **Start all microservices**
```bash
python start_services.py
```

This will start:
- User Service on port 8000
- Kraken Service on port 8001
- Bot Service should be started separately on port 8002

**For detailed setup instructions, see [SETUP.md](SETUP.md)**

## API Documentation

Once services are running, visit:
- User Service: http://localhost:8000/docs
- Kraken Service: http://localhost:8001/docs

## Project Structure

```
muckard-fastapi/
├── app/                    # Shared code (utilities, models, config)
│   ├── models/            # Shared database models
│   ├── schemas/           # Shared Pydantic schemas
│   ├── services/events/   # Event publishing infrastructure
│   └── utils/             # Shared utilities
├── services/              # Microservices
│   ├── user-service/      # User Service (port 8000)
│   └── kraken-service/    # Kraken Service (port 8001)
├── alembic/               # Centralized database migrations
├── .env                   # Configuration (not in git)
└── start_services.py      # Start all services
```

**For detailed structure, see [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**

## Messaging Architecture

### Kafka (Event Streaming)
- High-volume events (user lifecycle, trading events)
- Long-term retention (90 days)
- Multiple consumers
- Replayable events

### RabbitMQ (Commands & Real-time)
- Bot commands (`bot.start`, `bot.stop`)
- Real-time status updates
- Immediate alerts
- Single consumer per message

## Configuration

**ALL configuration must be in `.env` file - no hardcoded defaults.**

Required variables:
- `DATABASE_URL` - PostgreSQL connection string (shared)
- `SECRET_KEY` - JWT secret (auto-generated if not set)
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker address
- `RABBITMQ_HOST`, `RABBITMQ_PORT`, etc. - RabbitMQ configuration
- All other variables from `.env.example`

## Development

### Running Individual Services

```bash
# User Service
cd services/user-service
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Kraken Service
cd services/kraken-service
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Database Migrations

Migrations are centralized in `alembic/` and import models from all services:

```bash
# Generate new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Test messaging architecture
python test_messaging_architecture.py

# Verify services
python verify_services.py
```

## Migration Notes

The project has been migrated from a monolithic architecture to microservices:

- ✅ Old routes in `app/api/v1/` have been removed
- ✅ Old services in `app/services/` have been removed (except shared infrastructure)
- ✅ All functionality moved to microservices
- ✅ Centralized migrations set up
- ✅ Shared utilities remain in `app/utils/` and `app/services/events/`

## BMAD-METHOD V6

This project follows BMAD-METHOD V6 principles:
- **Agent-as-Code**: Each service is an independent agent
- **Two-Phase Pipeline**: Planning → Build/Verify
- **Modular Architecture**: Microservices design
- **Event-Driven**: Kafka and RabbitMQ for communication

See `../agents/` for agent definitions.

## Development Status

✅ **Microservices Architecture Complete** - All services operational

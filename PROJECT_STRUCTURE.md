# Microservices Architecture - Project Structure

## 📁 Complete Project Structure

```
muckard-fastapi/
├── app/                              # Shared code (utilities, models, config)
│   ├── __init__.py
│   ├── main.py                       # DEPRECATED - Use microservices instead
│   ├── config.py                     # Shared configuration (reads from .env)
│   ├── database.py                   # Shared database connection
│   │
│   ├── models/                       # Shared SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── kraken_key.py
│   │   ├── trade.py
│   │   ├── bot_status.py
│   │   ├── bot_execution.py
│   │   ├── notification.py
│   │   ├── support_ticket.py
│   │   ├── audit_log.py
│   │   ├── role.py
│   │   ├── permission.py
│   │   ├── role_permission.py
│   │   ├── user_role.py
│   │   └── otp.py
│   │
│   ├── schemas/                      # Shared Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── kraken.py
│   │   ├── trading_data.py
│   │   ├── bot_status.py
│   │   ├── dashboard.py
│   │   ├── admin.py
│   │   ├── notification.py
│   │   └── support.py
│   │
│   ├── services/                     # Shared infrastructure only
│   │   ├── __init__.py
│   │   └── events/                    # Event publishing infrastructure
│   │       ├── __init__.py
│   │       ├── event_publisher.py
│   │       ├── event_types.py
│   │       ├── factory.py
│   │       └── kafka_publisher.py
│   │
│   └── utils/                        # Shared utilities
│       ├── __init__.py
│       ├── security.py               # JWT, password hashing
│       ├── redis_client.py           # Redis caching
│       ├── vault_service.py           # HashiCorp Vault integration
│       ├── kraken_client.py          # Kraken API client
│       ├── validators.py             # Input validation
│       ├── event_publisher.py        # Unified event publisher (Kafka/RabbitMQ)
│       ├── kafka_consumer.py         # Kafka consumer utilities
│       └── rabbitmq_client.py        # RabbitMQ client utilities
│
├── services/                         # Microservices
│   │
│   ├── user-service/                 # User Service (Port 8000)
│   │   ├── main.py                   # Service entry point
│   │   ├── config.py                 # Service-specific config
│   │   ├── database.py               # Service database connection
│   │   │
│   │   ├── api/                      # API Routes
│   │   │   ├── __init__.py
│   │   │   ├── deps.py               # Dependencies (auth)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py           # Authentication endpoints
│   │   │       ├── onboarding.py     # Onboarding endpoints
│   │   │       └── profile.py        # Profile endpoints
│   │   │
│   │   ├── models/                   # Service-specific models
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User model (service-specific)
│   │   │   └── otp.py                # OTP model
│   │   │
│   │   ├── schemas/                  # Service-specific schemas
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   │
│   │   ├── services/                 # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py       # Authentication service
│   │   │   ├── user_service.py        # User management service
│   │   │   ├── otp_service.py         # OTP service
│   │   │   └── email_service.py       # Email service
│   │   │
│   │   └── utils/                    # Service-specific utilities
│   │       ├── security.py
│   │       ├── redis_client.py
│   │       └── rabbitmq_client.py
│   │
│   └── kraken-service/               # Kraken Service (Port 8001)
│       ├── main.py                   # Service entry point
│       ├── config.py                 # Service-specific config
│       ├── database.py               # Service database connection
│       │
│       ├── api/                      # API Routes
│       │   └── v1/                    # (Routes to be implemented)
│       │
│       ├── models/                   # Service-specific models (if any)
│       │
│       ├── schemas/                  # Service-specific schemas (if any)
│       │
│       ├── services/                 # Business logic
│       │   ├── __init__.py
│       │   ├── kraken_service.py     # Kraken integration service
│       │   ├── trading_data_service.py # Trading data service
│       │   ├── bot_status_service.py  # Bot status service
│       │   └── rabbitmq_consumer.py   # RabbitMQ consumer
│       │
│       └── utils/                    # Service-specific utilities
│           └── rabbitmq_client.py
│
├── alembic/                          # Centralized Database Migrations
│   ├── env.py                        # Imports models from all services
│   ├── script.py.mako
│   ├── README
│   └── versions/                     # Migration files
│
├── .env                              # Shared configuration (project root)
├── .env.example                      # Environment variables template
├── alembic.ini                       # Alembic configuration
├── requirements.txt                  # Python dependencies
├── start_services.py                # Script to start all microservices
├── verify_services.py               # Script to verify services
├── test_messaging_architecture.py   # Integration tests
├── README.md                         # Project documentation
└── PROJECT_STRUCTURE.md              # This file
```

## 🏗️ Architecture Overview

### Microservices

1. **User Service** (Port 8000)
   - Authentication (register, login, OTP verification)
   - User profile management
   - Onboarding flow
   - Publishes events: `user.created`, `user.updated`, `user.logged_in`, `onboarding.completed`

2. **Kraken Service** (Port 8001)
   - Kraken API key management
   - Trading data endpoints
   - Bot status management
   - Consumes: `user.created`, `bot.trade.executed`, `bot.trade.skipped`
   - Publishes: `kraken.key.connected`, `kraken.key.disconnected`, `kraken.key.updated`, `trade.executed`

3. **Bot Service** (Port 8002 - in `muckai/muckai/`)
   - Trading bot execution
   - Consumes: `bot.start`, `bot.stop`, `bot.trigger_trade` (from RabbitMQ)
   - Publishes: `bot.trade.executed`, `bot.trade.skipped` (to Kafka), `bot.started`, `bot.stopped`, `bot.error` (to RabbitMQ)

### Shared Infrastructure

- **`app/models/`**: Shared database models used by multiple services
- **`app/schemas/`**: Shared Pydantic schemas
- **`app/utils/`**: Shared utilities (event publisher, Kafka consumer, RabbitMQ client, etc.)
- **`app/services/events/`**: Event publishing infrastructure
- **`alembic/`**: Centralized migration system that imports models from all services

## 🔧 Configuration

**ALL configuration in `.env` file** - No hardcoded defaults!

Required variables:
- `APP_NAME`, `DEBUG`, `API_V1_PREFIX`
- `SECRET_KEY` (auto-generated if empty)
- `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
- `DATABASE_URL` (shared database)
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`
- `VAULT_URL`, `VAULT_TOKEN`, `VAULT_MOUNT_PATH`
- `KRAKEN_API_BASE_URL`
- `CORS_ORIGINS`
- `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_*` (Kafka configuration)
- `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_VHOST`

## 🚀 Quick Start

1. **Copy environment file:**
   ```bash
   cp env.example .env
   # Edit .env with your values
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations (centralized):**
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

4. **Start all microservices:**
   ```bash
   python start_services.py
   ```

   Or start individually:
   ```bash
   # User Service
   cd services/user-service
   uvicorn main:app --host 127.0.0.1 --port 8000

   # Kraken Service
   cd services/kraken-service
   uvicorn main:app --host 127.0.0.1 --port 8001
   ```

5. **Access API docs:**
   - User Service: http://localhost:8000/docs
   - Kraken Service: http://localhost:8001/docs

## 📊 Database Schema

All services share the same PostgreSQL database. Models are defined in:
- `app/models/` - Shared models
- `services/user-service/models/` - User service models
- `services/kraken-service/models/` - Kraken service models (if any)

Centralized migrations in `alembic/` import models from all services.

## 🔄 Messaging Architecture

### Kafka (Event Streaming)
- `user.events` - User lifecycle events
- `onboarding.events` - Onboarding events
- `kraken.events` - Kraken API events
- `trading.events` - Trading events

### RabbitMQ (Commands & Real-time)
- `bot.start`, `bot.stop`, `bot.trigger_trade` - Bot commands
- `bot.started`, `bot.stopped`, `bot.error` - Bot status updates
- `kraken.key.test.failed` - Alerts

## ✨ Features

- ✅ Microservices architecture
- ✅ Centralized database migrations
- ✅ Hybrid messaging (Kafka + RabbitMQ)
- ✅ Event-driven communication
- ✅ JWT-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Redis caching
- ✅ HashiCorp Vault integration (optional)
- ✅ PostgreSQL database (shared)
- ✅ CORS configuration
- ✅ Structured logging
- ✅ Service resilience (graceful degradation)

## 🔒 Security

- Password hashing with bcrypt
- JWT tokens (access + refresh)
- API keys encrypted in Vault
- No withdrawal permissions on API keys
- Admin-only endpoints protected
- CORS configured

## 📝 Migration from Monolithic

The old monolithic code in `app/api/v1/` and `app/services/` has been removed. All functionality is now in microservices:
- User Service handles all authentication and user management
- Kraken Service handles all Kraken API and trading operations
- Shared utilities remain in `app/utils/` and `app/services/events/`

---

**Status**: ✅ Microservices Architecture Complete

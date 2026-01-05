# Complete Testing Guide - Local Development

Complete guide for testing the Muckard microservices architecture in your local environment.

## Prerequisites

### 1. Infrastructure Services

Ensure the following services are running:

- **PostgreSQL** (database) - Port 5432
- **Redis** (cache) - Port 6379
- **Kafka** (event streaming) - Port 9092
- **RabbitMQ** (commands & real-time) - Ports 5672 (AMQP), 15672 (Management UI)

### 2. Environment Setup

1. **Create `.env` file:**

   ```bash
   # Copy the example file
   cp env.example .env
   ```

2. **Configure required variables in `.env`:**

   - `DATABASE_URL` - PostgreSQL connection string
   - `SECRET_KEY` - JWT secret (auto-generated if empty)
   - `REDIS_HOST`, `REDIS_PORT` - Redis configuration
   - `KAFKA_BOOTSTRAP_SERVERS` - Kafka broker address
   - `RABBITMQ_HOST`, `RABBITMQ_PORT`, etc. - RabbitMQ configuration
   - `CORS_ORIGINS` - Allowed frontend origins

3. **Configure Kraken API Keys:**

   - `KRAKEN_API_KEY_READONLY` - Read-only API key (for development)
   - `KRAKEN_API_SECRET_READONLY` - Read-only API secret
   - `KRAKEN_KEY_MODE=readonly` - Use readonly keys for development

   **Important:** See [API_KEYS.md](API_KEYS.md) for detailed Kraken API key configuration.

4. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 3. Database Setup

```bash
# Run database migrations
alembic upgrade head
```

## Complete Testing Workflow

### Step 1: Start Infrastructure Services

```bash
# Start all infrastructure services (PostgreSQL, Redis, Kafka, RabbitMQ)
docker-compose -f docker-compose.infrastructure.yml up -d

# Or start individually:
# PostgreSQL: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
# Redis: docker run -d -p 6379:6379 redis
# RabbitMQ: docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:management
```

### Step 2: Verify Infrastructure

```bash
# Check if all infrastructure is running
python verify_services.py
```

This will verify:

- ✅ Python dependencies installed
- ✅ Service modules can be imported
- ✅ Database connectivity
- ✅ Redis connectivity
- ✅ Kafka connectivity
- ✅ RabbitMQ connectivity

### Step 3: Start All Microservices

```bash
# Start User Service (8000) and Kraken Service (8001)
python start_services.py
```

This will:

- Start User Service on port 8000
- Start Kraken Service on port 8001
- Display service logs
- Verify services are running

**Or start individually:**

```bash
# Terminal 1 - User Service
cd services/user-service
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - Kraken Service
cd services/kraken-service
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Step 4: Verify Services Are Running

```bash
# Check User Service
curl http://localhost:8000/user

# Check Kraken Service
curl http://localhost:8001/kraken
```

Both should return: `{"status": "ok", "message": "Service is running"}`

## Manual Testing

### 1. Test User Service

#### Health Check

```bash
curl http://localhost:8000/user
```

#### Register User

```bash
curl -X POST http://localhost:8000/user/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234!",
    "name": "Test User"
  }'
```

Expected response: `{"message": "User registered successfully", "user_id": "..."}`

#### Login User

**Important:** Login uses form-encoded data, not JSON.

```bash
curl -X POST http://localhost:8000/user/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test1234!"
```

Or using `curl` with `--data-urlencode`:

```bash
curl -X POST http://localhost:8000/user/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=test@example.com" \
  --data-urlencode "password=Test1234!"
```

Expected response: `{"access_token": "...", "token_type": "bearer"}`

**Save the `access_token` for authenticated requests.**

#### Get Current User (Requires Authentication)

```bash
# Replace YOUR_TOKEN with the access_token from login
curl -X GET http://localhost:8000/user/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Complete Onboarding

```bash
curl -X POST http://localhost:8000/user/api/v1/onboarding \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trading_experience": "intermediate",
    "risk_tolerance": "moderate",
    "investment_goals": "growth"
  }'
```

#### View API Documentation

Open in browser: http://localhost:8000/docs

### 2. Test Kraken Service

#### Health Check

```bash
curl http://localhost:8001/kraken
```

#### Connect Kraken API Key

```bash
curl -X POST http://localhost:8001/api/v1/kraken/connect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "My Kraken Key",
    "api_key": "YOUR_KRAKEN_API_KEY",
    "api_secret": "YOUR_KRAKEN_API_SECRET"
  }'
```

#### List Kraken Keys

```bash
curl -X GET http://localhost:8001/api/v1/kraken/keys \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Trading Data

```bash
curl -X GET http://localhost:8001/api/v1/trading/pairs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### View API Documentation

Open in browser: http://localhost:8001/docs

### 3. Test Kraken API Key Configuration

#### Verify Keys Are Loaded

```python
python -c "
from app.config import settings
print(f'Key Mode: {settings.KRAKEN_KEY_MODE}')
print(f'Read-only key loaded: {bool(settings.KRAKEN_API_KEY_READONLY)}')
print(f'Trading key loaded: {bool(settings.KRAKEN_API_KEY_TRADING)}')
print(f'Selected key (first 10 chars): {settings.kraken_api_key[:10] if settings.kraken_api_key else \"None\"}...')
"
```

#### Test Key Mode Selection

```python
python -c "
from app.config import settings
print(f'Current mode: {settings.KRAKEN_KEY_MODE}')
print(f'API Key: {settings.kraken_api_key[:20] if settings.kraken_api_key else \"Not set\"}...')
print(f'API Secret: {settings.kraken_api_secret[:20] if settings.kraken_api_secret else \"Not set\"}...')
"
```

#### Test Safety Checks

When `KrakenClient` is initialized, it will automatically validate the key mode and warn if trading keys are used in DEBUG mode.

### 4. Test Database Migrations

```bash
# Check current migration status
alembic current

# Create new migration (if models changed)
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### 5. Verify Kafka Events

#### Install Kafka Python Client (if needed)

```bash
pip install kafka-python
```

#### Consume Events from Topics

```python
python -c "
from kafka import KafkaConsumer
import json

# Consume user events
consumer = KafkaConsumer(
    'user.events',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print('Listening for user.events...')
for message in consumer:
    print(f'Received: {message.value}')
    break  # Exit after first message
"
```

#### List All Kafka Topics

```bash
# If using Docker
docker exec -it kafka-container kafka-topics --list --bootstrap-server localhost:9092

# Or using kafka-python
python -c "
from kafka.admin import KafkaAdminClient
admin = KafkaAdminClient(bootstrap_servers='localhost:9092')
topics = admin.list_topics()
print('Topics:', topics)
"
```

#### Verify Events After Actions

After registering a user:

```bash
# Should see user.created event in user.events topic
```

After logging in:

```bash
# Should see user.logged_in event in user.events topic
```

After completing onboarding:

```bash
# Should see onboarding.completed event in onboarding.events topic
```

After connecting Kraken key:

```bash
# Should see kraken.key.connected event in kraken.events topic
```

### 6. Verify RabbitMQ

#### Access Management UI

Open in browser: http://localhost:15672

- Username: `guest`
- Password: `guest`

#### View Queues and Messages

- Navigate to "Queues" tab
- Check for bot command queues
- View message details

#### Test Bot Commands (via API)

```bash
# Start bot (requires authentication)
curl -X POST http://localhost:8001/api/v1/bot/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Stop bot
curl -X POST http://localhost:8001/api/v1/bot/stop \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## Complete Integration Test Scenarios

### Scenario 1: Complete User Onboarding Flow

1. **Register User**

   ```bash
   curl -X POST http://localhost:8000/user/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "Test1234!", "name": "Test User"}'
   ```

   - ✅ Should return user ID
   - ✅ Should publish `user.created` event to Kafka

2. **Login User**

   ```bash
   curl -X POST http://localhost:8000/user/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=Test1234!"
   ```

   - ✅ Should return access token
   - ✅ Should publish `user.logged_in` event to Kafka

3. **Complete Onboarding**

   ```bash
   curl -X POST http://localhost:8000/user/api/v1/onboarding \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"trading_experience": "intermediate", "risk_tolerance": "moderate"}'
   ```

   - ✅ Should return success
   - ✅ Should publish `onboarding.completed` event to Kafka

4. **Connect Kraken Key**
   ```bash
   curl -X POST http://localhost:8001/api/v1/kraken/connect \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"key_name": "My Key", "api_key": "YOUR_KEY", "api_secret": "YOUR_SECRET"}'
   ```
   - ✅ Should return key ID
   - ✅ Should publish `kraken.key.connected` event to Kafka

### Scenario 2: Trading Data Flow

1. **Get Trading Pairs**

   ```bash
   curl -X GET http://localhost:8001/api/v1/trading/pairs \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

   - ✅ Should return list of trading pairs

2. **Get Live Trading Data**

   ```bash
   curl -X GET http://localhost:8001/api/v1/trading/live?pair=BTC/USD \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

   - ✅ Should return live trading data

3. **Get Account Balance**
   ```bash
   curl -X GET http://localhost:8001/api/v1/trading/balance \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
   - ✅ Should return account balance

### Scenario 3: Event Consumption Verification

1. **Verify Kafka Events**

   - Check `user.events` topic for user lifecycle events
   - Check `kraken.events` topic for Kraken key events
   - Check `trading.events` topic for trading events
   - Check `onboarding.events` topic for onboarding events

2. **Verify RabbitMQ Messages**

   - Check RabbitMQ Management UI for bot command queues
   - Verify messages are delivered when bot commands are sent

3. **Verify Service Logs**
   - Check User Service logs for event publishing
   - Check Kraken Service logs for event consumption
   - Check for any error messages

## Troubleshooting

### Services Not Starting

**Check if ports are in use:**

```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :8001

# Linux/Mac
lsof -i :8000
lsof -i :8001
```

**Check service logs:**

- Look at the terminal output from `start_services.py`
- Check for import errors or configuration issues

### Database Connection Issues

**Test database connection:**

```python
python -c "
from app.config import settings
from sqlalchemy import create_engine
try:
    engine = create_engine(settings.DATABASE_URL)
    conn = engine.connect()
    print('[OK] Database connected!')
    conn.close()
except Exception as e:
    print(f'[ERROR] Database connection failed: {e}')
"
```

**Common issues:**

- PostgreSQL not running
- Wrong `DATABASE_URL` in `.env`
- Database doesn't exist (create it first)

### Kafka Not Working

**Check if Kafka is running:**

```bash
# Docker
docker ps | grep kafka

# List topics
docker exec -it kafka-container kafka-topics --list --bootstrap-server localhost:9092
```

**Common issues:**

- Kafka not started
- Wrong `KAFKA_BOOTSTRAP_SERVERS` in `.env`
- Network connectivity issues

### RabbitMQ Not Working

**Check if RabbitMQ is running:**

```bash
# Docker
docker ps | grep rabbitmq

# Access management UI
# http://localhost:15672 (guest/guest)
```

**Common issues:**

- RabbitMQ not started
- Wrong credentials in `.env`
- Port conflicts

### Authentication Issues

**Login fails:**

- Ensure using form-encoded data (`application/x-www-form-urlencoded`)
- Use `username` field (not `email`)
- Check password is correct

**Token expired:**

- Tokens expire after 30 minutes (default)
- Re-login to get new token

### Kraken API Key Issues

**Keys not loading:**

- Check `.env` file has `KRAKEN_API_KEY_READONLY` and `KRAKEN_API_SECRET_READONLY`
- Verify `KRAKEN_KEY_MODE=readonly` for development
- Restart services after changing `.env`

**Key connection fails:**

- Verify API keys are valid
- Check key permissions (read-only keys cannot execute trades)
- See [API_KEYS.md](API_KEYS.md) for detailed troubleshooting

**Safety warnings:**

- If you see warnings about trading keys in DEBUG mode, set `KRAKEN_KEY_MODE=readonly` in `.env`

### API Endpoint Not Found (404)

**Check endpoint paths:**

- User Service: `/user/api/v1/*` (not `/api/v1/*`)
- Kraken Service: `/api/v1/kraken/*`, `/api/v1/trading/*`, etc.
- Health checks: `/user` and `/kraken` (not `/`)

**Verify service is running:**

```bash
curl http://localhost:8000/user
curl http://localhost:8001/kraken
```

## Utility Scripts Reference

| Script               | Purpose                                             |
| -------------------- | --------------------------------------------------- |
| `start_services.py`  | Start all microservices                             |
| `verify_services.py` | Verify dependencies and infrastructure connectivity |

## Expected Test Results

When everything is working correctly, you should see:

```
✅ Infrastructure services running (PostgreSQL, Redis, Kafka, RabbitMQ)
✅ User Service running on port 8000
✅ Kraken Service running on port 8001
✅ User registration successful
✅ User login successful (returns access token)
✅ Onboarding completed
✅ Kraken key connected
✅ Kafka events published (user.created, user.logged_in, onboarding.completed, kraken.key.connected)
✅ RabbitMQ queues accessible
✅ Trading data endpoints working
```

## Next Steps

After completing local testing:

1. **Review service logs** for any errors or warnings
2. **Check Kafka topics** for event publishing
3. **Check RabbitMQ queues** for message delivery
4. **Verify database records** were created correctly
5. **Test error scenarios** (invalid credentials, missing data, etc.)
6. **Test edge cases** (duplicate emails, invalid API keys, etc.)

## Additional Resources

- **API Documentation:**

  - User Service: http://localhost:8000/docs
  - Kraken Service: http://localhost:8001/docs

- **Configuration Guides:**

  - [API_KEYS.md](API_KEYS.md) - Kraken API key configuration
  - [README.md](README.md) - Project overview
  - [SETUP.md](SETUP.md) - Detailed setup instructions

- **Infrastructure Management:**
  - RabbitMQ Management UI: http://localhost:15672 (guest/guest)
  - Kafka topics can be viewed via Docker or kafka-python

---

**Happy Testing! 🚀**

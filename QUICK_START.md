# 🚀 Quick Start Guide

## 1. Setup (5 minutes)

```bash
# Navigate to project
cd fastapi-backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Edit .env - MINIMUM REQUIRED:
# - DATABASE_URL (PostgreSQL connection)
# - REDIS_HOST (usually localhost)
# - CORS_ORIGINS (your frontend URLs)
```

## 2. Database Setup

```bash
# Create PostgreSQL database
createdb muckard_db

# Run migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## 3. Start Services

```bash
# Terminal 1: Start Redis (if not running as service)
redis-server

# Terminal 2: Start FastAPI
uvicorn app.main:app --reload
```

## 4. Test API

Visit: http://localhost:8000/docs

Try these endpoints:
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user (requires auth)

## ✅ You're Ready!

The FastAPI backend is now running with:
- ✅ 80+ API endpoints
- ✅ JWT authentication
- ✅ Database models (12 tables)
- ✅ Redis caching
- ✅ Clean architecture
- ✅ All configuration in `.env`

## 📚 Documentation

- **Full Setup**: See [SETUP.md](SETUP.md)
- **Project Structure**: See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- **API Spec**: See [BMAD-METHOD-V6-SPEC.md](../BMAD-METHOD-V6-SPEC.md)

## 🐛 Troubleshooting

**Database Error?**
- Check PostgreSQL is running
- Verify `DATABASE_URL` in `.env`

**Redis Error?**
- Check Redis is running
- Verify `REDIS_HOST` in `.env`

**Import Error?**
- Activate virtual environment
- Run `pip install -r requirements.txt`


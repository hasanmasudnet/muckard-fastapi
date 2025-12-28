# FastAPI Backend for Muckard Trading Platform

FastAPI backend API serving both `dev.muckard.com` and `admin.muckard.com` frontends.

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

4. **Run database migrations**
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

5. **Start development server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**For detailed setup instructions, see [SETUP.md](SETUP.md)**

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
fastapi-backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration (reads from .env)
│   ├── database.py          # Database setup
│   ├── api/                 # API routes
│   │   ├── deps.py          # Dependencies (auth, etc.)
│   │   └── v1/              # API v1 routes
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic (Agents)
│   └── utils/               # Utilities
├── .env                     # Your configuration (not in git)
├── .env.example             # Configuration template
└── requirements.txt         # Python dependencies
```

## BMAD-METHOD V6

This project follows BMAD-METHOD V6 principles:
- **Agent-as-Code**: Each agent defined in `agents/` directory
- **Two-Phase Pipeline**: Planning → Build/Verify
- **Modular Architecture**: Service-oriented design

See `../agents/` for agent definitions.

## Configuration

**ALL configuration must be in `.env` file - no hardcoded defaults.**

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret (auto-generated if not set)
- All other variables from `.env.example`

## Development Status

🚧 **In Development** - Following BMAD-METHOD V6 specification


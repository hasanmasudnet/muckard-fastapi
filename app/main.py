from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import sys
from app.config import settings
from app.database import get_db
from app.api.v1 import auth, kraken, trading_data, bot_status, dashboard, profile, admin, onboarding
from app.services.events.factory import get_event_publisher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting FastAPI application...")

app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI Backend for Muckard Trading Platform",
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["http://localhost:3000"],  # Ensure localhost:3000 is included
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Authentication"])
app.include_router(kraken.router, prefix=settings.API_V1_PREFIX, tags=["Kraken"])
app.include_router(trading_data.router, prefix=settings.API_V1_PREFIX, tags=["Trading Data"])
app.include_router(bot_status.router, prefix=settings.API_V1_PREFIX, tags=["Bot Status"])
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX, tags=["Dashboard"])
app.include_router(profile.router, prefix=settings.API_V1_PREFIX, tags=["Profile"])
app.include_router(onboarding.router, prefix=settings.API_V1_PREFIX, tags=["Onboarding"])
app.include_router(admin.router, prefix=settings.API_V1_PREFIX, tags=["Admin"])

# Global event publisher instance
event_publisher = None


@app.get("/")
async def root():
    return {
        "message": "FastAPI Backend API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    global event_publisher
    try:
        event_publisher = get_event_publisher()
        logger.info("Event publisher initialized")
    except Exception as e:
        logger.error(f"Failed to initialize event publisher: {e}", exc_info=True)
        event_publisher = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    global event_publisher
    if event_publisher and hasattr(event_publisher, 'flush'):
        try:
            event_publisher.flush()
            logger.info("Event publisher flushed")
        except Exception as e:
            logger.error(f"Error flushing event publisher: {e}", exc_info=True)


@app.get("/health/db")
async def health_check_db(db: Session = Depends(get_db)):
    """Database health check"""
    from sqlalchemy import text
    try:
        # Test database connection
        result = db.execute(text("SELECT 1"))
        result.scalar()
        
        # Get database info
        db_info = db.execute(text("SELECT version(), current_database()"))
        version, db_name = db_info.fetchone()
        
        # Count tables
        table_count = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)).scalar()
        
        return {
            "status": "healthy",
            "database": {
                "connected": True,
                "name": db_name,
                "version": version.split(',')[0],  # Just the PostgreSQL version
                "tables_count": table_count
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": {
                "connected": False,
                "error": str(e)
            }
        }


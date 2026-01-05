from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.v1 import auth, profile, onboarding
from config import settings
import logging
import traceback

logger = logging.getLogger(__name__)

app = FastAPI(title="muckard - user service")

# Add global exception handler to see actual errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Match muckard-backend route pattern
app.include_router(auth.router, prefix="/user/api/v1/auth", tags=["Authentication"])
app.include_router(onboarding.router, prefix="/user/api/v1", tags=["Onboarding"])
app.include_router(profile.router, prefix="/user/api/v1", tags=["Profile"])

@app.get("/user", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "message": "User service is running"}


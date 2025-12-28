from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import require_admin
from app.schemas.user import UserResponse

router = APIRouter(prefix="/admin")


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    # TODO: Implement user listing
    return {"message": "User listing not yet implemented", "page": page, "page_size": page_size}


@router.get("/stats")
async def get_system_stats(
    current_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics (admin only)"""
    # TODO: Implement system stats
    return {"message": "System stats not yet implemented"}


@router.get("/health")
async def get_system_health(
    current_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system health (admin only)"""
    # TODO: Implement health check
    return {"status": "healthy"}


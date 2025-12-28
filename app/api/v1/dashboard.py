from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService
from app.api.deps import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(prefix="/dashboard")


@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_dashboard_data(current_user.id)


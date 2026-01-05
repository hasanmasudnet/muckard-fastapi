from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserResponse, UserUpdate
from services.user_service import UserService
from api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=UserResponse)
async def get_profile(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    user_service = UserService(db)
    return await user_service.get_user_profile(current_user.id)


@router.put("", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user_service = UserService(db)
    return await user_service.update_user_profile(current_user.id, user_data)


@router.put("/password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    user_service = UserService(db)
    return await user_service.change_password(current_user.id, old_password, new_password)


@router.get("/activity")
async def get_activity_log(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user activity log"""
    # TODO: Implement activity log
    return {"message": "Activity log not yet implemented"}


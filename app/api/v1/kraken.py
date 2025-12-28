from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.kraken import KrakenKeyCreate, KrakenKeyResponse, KrakenKeyUpdate, KrakenConnectionTest
from app.services.kraken_service import KrakenService
from app.api.deps import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(prefix="/kraken")


@router.post("/connect", response_model=KrakenKeyResponse, status_code=status.HTTP_201_CREATED)
async def connect_kraken_key(
    key_data: KrakenKeyCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect and store Kraken API key"""
    kraken_service = KrakenService(db)
    return await kraken_service.connect_key(current_user.id, key_data)


@router.get("/keys", response_model=List[KrakenKeyResponse])
async def list_kraken_keys(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's Kraken API keys"""
    kraken_service = KrakenService(db)
    return await kraken_service.list_user_keys(current_user.id)


@router.get("/keys/{key_id}", response_model=KrakenKeyResponse)
async def get_kraken_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific Kraken API key info"""
    kraken_service = KrakenService(db)
    return await kraken_service.get_key(key_id, current_user.id)


@router.post("/keys/{key_id}/test", response_model=KrakenConnectionTest)
async def test_kraken_connection(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test Kraken API connection"""
    kraken_service = KrakenService(db)
    return await kraken_service.test_connection(key_id, current_user.id)


@router.put("/keys/{key_id}", response_model=KrakenKeyResponse)
async def update_kraken_key(
    key_id: str,
    key_data: KrakenKeyUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update Kraken API key settings"""
    kraken_service = KrakenService(db)
    return await kraken_service.update_key(key_id, current_user.id, key_data)


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kraken_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove Kraken API key"""
    kraken_service = KrakenService(db)
    await kraken_service.delete_key(key_id, current_user.id)
    return None


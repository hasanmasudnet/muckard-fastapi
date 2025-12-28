from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException, status
from typing import Optional
import uuid
from app.models.kraken_key import KrakenKey
from app.schemas.kraken import KrakenKeyCreate, KrakenKeyUpdate, KrakenKeyResponse, KrakenConnectionTest
from app.utils.vault_service import VaultService
from app.utils.kraken_client import KrakenClient
from app.utils.validators import validate_kraken_api_key, validate_kraken_api_secret


class KrakenService:
    """Kraken Integration Agent - Service Layer"""
    
    def __init__(self, db: Session):
        self.db = db
        try:
            self.vault = VaultService()
        except ImportError:
            self.vault = None  # Vault optional for development

    async def connect_key(self, user_id: uuid.UUID, key_data: KrakenKeyCreate) -> KrakenKeyResponse:
        """Store and validate Kraken API key"""
        # Validate API key format
        if not validate_kraken_api_key(key_data.api_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid API key format"
            )
        if not validate_kraken_api_secret(key_data.api_secret):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid API secret format"
            )

        # Test connection
        kraken_client = KrakenClient(key_data.api_key, key_data.api_secret)
        try:
            test_result = await kraken_client.test_connection()
            permissions = await kraken_client.validate_permissions()
            
            # Ensure no withdrawal permissions
            if permissions.get("has_withdraw", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API key must not have withdrawal permissions"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect to Kraken: {str(e)}"
            )
        finally:
            await kraken_client.close()

        # Store encrypted keys in Vault
        vault_path = f"kraken/{user_id}/{key_data.key_name}"
        if self.vault:
            try:
                self.vault.store_secret(vault_path, {
                    "api_key": key_data.api_key,
                    "api_secret": key_data.api_secret
                })
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to store keys in Vault: {str(e)}"
                )
        else:
            # Development mode: store in database (NOT RECOMMENDED FOR PRODUCTION)
            # In production, Vault is required
            pass

        # Create database record
        db_key = KrakenKey(
            user_id=user_id,
            key_name=vault_path,
            connection_status="connected",
            last_tested_at=datetime.now(timezone.utc)
        )
        self.db.add(db_key)
        self.db.commit()
        self.db.refresh(db_key)
        return KrakenKeyResponse.model_validate(db_key)

    async def list_user_keys(self, user_id: uuid.UUID) -> list[KrakenKeyResponse]:
        """List all Kraken keys for a user"""
        keys = self.db.query(KrakenKey).filter(KrakenKey.user_id == user_id).all()
        return [KrakenKeyResponse.model_validate(key) for key in keys]

    async def get_key(self, key_id: str, user_id: uuid.UUID) -> KrakenKeyResponse:
        """Get specific key info"""
        try:
            key_uuid = uuid.UUID(key_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid key ID format"
            )

        key = self.db.query(KrakenKey).filter(
            KrakenKey.id == key_uuid,
            KrakenKey.user_id == user_id
        ).first()

        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kraken key not found"
            )

        return KrakenKeyResponse.model_validate(key)

    async def test_connection(self, key_id: str, user_id: uuid.UUID) -> KrakenConnectionTest:
        """Test Kraken API connection"""
        key = await self.get_key(key_id, user_id)
        
        # Retrieve keys from Vault
        if self.vault:
            try:
                secrets = self.vault.get_secret(key.key_name)
                api_key = secrets["api_key"]
                api_secret = secrets["api_secret"]
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve keys from Vault: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vault service not available"
            )

        # Test connection
        kraken_client = KrakenClient(api_key, api_secret)
        try:
            test_result = await kraken_client.test_connection()
            status_str = "connected" if test_result.get("status") == "connected" else "failed"
            
            # Update last tested
            key.last_tested_at = datetime.now(timezone.utc)
            key.connection_status = status_str
            self.db.commit()
            
            return KrakenConnectionTest(
                status=status_str,
                tested_at=key.last_tested_at,
                message="Connection successful" if status_str == "connected" else "Connection failed"
            )
        except Exception as e:
            key.connection_status = "failed"
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection test failed: {str(e)}"
            )
        finally:
            await kraken_client.close()

    async def update_key(self, key_id: str, user_id: uuid.UUID, key_data: KrakenKeyUpdate) -> KrakenKeyResponse:
        """Update key settings"""
        key = await self.get_key(key_id, user_id)
        
        if key_data.key_name is not None:
            key.key_name = key_data.key_name
        if key_data.is_active is not None:
            key.is_active = key_data.is_active
        
        key.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(key)
        return KrakenKeyResponse.model_validate(key)

    async def delete_key(self, key_id: str, user_id: uuid.UUID) -> None:
        """Delete Kraken key"""
        key = await self.get_key(key_id, user_id)
        
        # Delete from Vault
        if self.vault:
            try:
                self.vault.delete_secret(key.key_name)
            except Exception as e:
                # Log error but continue with database deletion
                pass
        
        # Delete from database
        self.db.delete(key)
        self.db.commit()


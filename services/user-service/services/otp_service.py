import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
import random
import logging
from models.otp import OTPVerification
from utils.redis_client import RedisClient
from services.email_service import EmailService

logger = logging.getLogger(__name__)


class OTPService:
    """Service for OTP generation, storage, and verification"""
    
    OTP_EXPIRY_MINUTES = 10
    REDIS_KEY_PREFIX = "otp:"
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = RedisClient()
        self.email_service = EmailService()
    
    def generate_otp(self) -> str:
        """Generate a random 6-digit OTP code"""
        return f"{random.randint(100000, 999999)}"
    
    def _get_redis_key(self, email: str) -> str:
        """Get Redis key for OTP"""
        return f"{self.REDIS_KEY_PREFIX}{email}"
    
    async def create_otp(self, email: str, name: str) -> OTPVerification:
        """
        Create and store OTP for email verification
        
        Args:
            email: User's email address
            name: User's name (for email personalization)
            
        Returns:
            OTPVerification: Created OTP record
        """
        logger.info(f"[OTP_SERVICE] create_otp called for email: {email}, name: {name}")
        
        # Invalidate any existing OTP for this email
        logger.debug(f"[OTP_SERVICE] Invalidating existing OTPs for: {email}")
        await self._invalidate_existing_otp(email)
        
        # Generate new OTP
        logger.debug(f"[OTP_SERVICE] Generating new OTP code")
        otp_code = self.generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        logger.info(f"[OTP_SERVICE] Generated OTP code: {otp_code}, expires at: {expires_at}")
        
        # Store in database
        logger.debug(f"[OTP_SERVICE] Storing OTP in database")
        otp_record = OTPVerification(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            is_verified=False
        )
        self.db.add(otp_record)
        self.db.commit()
        self.db.refresh(otp_record)
        logger.info(f"[OTP_SERVICE] OTP stored in database. ID: {otp_record.id}")
        
        # Store in Redis for fast lookup (TTL: 10 minutes = 600 seconds)
        try:
            redis_key = self._get_redis_key(email)
            otp_data = {
                "otp_code": otp_code,
                "otp_id": str(otp_record.id),
                "expires_at": expires_at.isoformat()
            }
            self.redis_client.set(redis_key, otp_data, ttl=600)
            logger.info(f"[OTP_SERVICE] OTP stored in Redis with key: {redis_key}")
        except Exception as e:
            logger.warning(f"[OTP_SERVICE] Failed to store OTP in Redis: {str(e)}. Continuing with database-only storage.")
        
        # Send email
        logger.info(f"[OTP_SERVICE] Calling email_service.send_otp_email for: {email}")
        email_sent = self.email_service.send_otp_email(email, otp_code, name)
        if email_sent:
            logger.info(f"[OTP_SERVICE] Email sent successfully to {email}")
        else:
            logger.warning(f"[OTP_SERVICE] Failed to send OTP email to {email}, but OTP was created. OTP code: {otp_code}")
        
        return otp_record
    
    async def _invalidate_existing_otp(self, email: str):
        """Invalidate any existing unverified OTP for this email"""
        # Mark existing OTPs as expired in database
        existing_otps = self.db.query(OTPVerification).filter(
            OTPVerification.email == email,
            OTPVerification.is_verified == False,
            OTPVerification.expires_at > datetime.now(timezone.utc)
        ).all()
        
        for otp in existing_otps:
            otp.is_verified = True  # Mark as used to prevent reuse
            otp.verified_at = datetime.now(timezone.utc)
        
        if existing_otps:
            self.db.commit()
        
        # Delete from Redis
        redis_key = self._get_redis_key(email)
        self.redis_client.delete(redis_key)
    
    async def verify_otp(self, email: str, otp_code: str) -> bool:
        """
        Verify OTP code for email
        
        Args:
            email: User's email address
            otp_code: 6-digit OTP code to verify
            
        Returns:
            bool: True if OTP is valid, False otherwise
        """
        # First check Redis for fast lookup
        redis_key = self._get_redis_key(email)
        cached_otp = self.redis_client.get(redis_key)
        
        if cached_otp:
            if cached_otp.get("otp_code") == otp_code:
                # Verify in database
                otp_id = cached_otp.get("otp_id")
                otp_record = self.db.query(OTPVerification).filter(
                    OTPVerification.id == otp_id,
                    OTPVerification.email == email,
                    OTPVerification.otp_code == otp_code,
                    OTPVerification.is_verified == False,
                    OTPVerification.expires_at > datetime.now(timezone.utc)
                ).first()
                
                if otp_record:
                    # Mark as verified
                    otp_record.is_verified = True
                    otp_record.verified_at = datetime.now(timezone.utc)
                    self.db.commit()
                    
                    # Delete from Redis
                    self.redis_client.delete(redis_key)
                    
                    return True
        
        # Fallback to database lookup if not in Redis
        otp_record = self.db.query(OTPVerification).filter(
            OTPVerification.email == email,
            OTPVerification.otp_code == otp_code,
            OTPVerification.is_verified == False,
            OTPVerification.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if otp_record:
            # Mark as verified
            otp_record.is_verified = True
            otp_record.verified_at = datetime.now(timezone.utc)
            self.db.commit()
            
            # Delete from Redis if exists
            self.redis_client.delete(redis_key)
            
            return True
        
        return False
    
    async def resend_otp(self, email: str, name: str) -> OTPVerification:
        """
        Resend OTP code (invalidates old, creates new)
        
        Args:
            email: User's email address
            name: User's name (for email personalization)
            
        Returns:
            OTPVerification: New OTP record
        """
        return await self.create_otp(email, name)


try:
    import hvac
    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False
    hvac = None

from app.config import settings
from typing import Dict, Any


class VaultService:
    """HashiCorp Vault service for encrypted key storage"""
    
    def __init__(self):
        if not HVAC_AVAILABLE:
            raise ImportError(
                "hvac package is required for VaultService. "
                "Install it with: pip install hvac"
            )
        self.client = hvac.Client(url=settings.VAULT_URL)
        if settings.VAULT_TOKEN:
            self.client.token = settings.VAULT_TOKEN

    def store_secret(self, path: str, secret: Dict[str, Any]) -> None:
        """Store secret in Vault"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret,
                mount_point=settings.VAULT_MOUNT_PATH
            )
        except Exception as e:
            raise Exception(f"Failed to store secret in Vault: {str(e)}")

    def get_secret(self, path: str) -> Dict[str, Any]:
        """Retrieve secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=settings.VAULT_MOUNT_PATH
            )
            return response["data"]["data"]
        except Exception as e:
            raise Exception(f"Failed to retrieve secret from Vault: {str(e)}")

    def delete_secret(self, path: str) -> None:
        """Delete secret from Vault"""
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=settings.VAULT_MOUNT_PATH
            )
        except Exception as e:
            raise Exception(f"Failed to delete secret from Vault: {str(e)}")

    def update_secret(self, path: str, secret: Dict[str, Any]) -> None:
        """Update secret in Vault"""
        self.store_secret(path, secret)


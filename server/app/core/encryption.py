from cryptography.fernet import Fernet
import base64
import os
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class EncryptionService:
    _instance = None
    _fernet = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Fernet cipher with encryption key"""
        key = os.getenv("ENCRYPTION_KEY")
        environment = os.getenv("ENVIRONMENT", "development")

        if not key:
            # Production: fail fast
            if environment == "production":
                raise ValueError(
                    "ENCRYPTION_KEY must be set in production environment.\n"
                    "Generate a key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'\n"
                    "Then add to .env: ENCRYPTION_KEY=<generated_key>"
                )

            # Development: generate temporary key with loud warning
            key = Fernet.generate_key().decode()
            logger.warning(
                f"\n{'='*70}\n"
                f"⚠️  ENCRYPTION_KEY NOT SET - GENERATED TEMPORARY KEY\n"
                f"{'='*70}\n"
                f"Key: {key}\n"
                f"Add to .env: ENCRYPTION_KEY={key}\n"
                f"{'='*70}\n"
            )

        try:
            # Validate and create Fernet instance
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string and return base64 encoded result"""
        if not plaintext:
            return ""

        encrypted = self._fernet.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt base64 encoded encrypted text"""
        if not encrypted_text:
            return ""

        try:
            encrypted_bytes = base64.b64decode(encrypted_text.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data. Key may have changed.")


encryption_service = EncryptionService()

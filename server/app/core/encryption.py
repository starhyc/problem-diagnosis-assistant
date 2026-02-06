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

        if not key:
            # Auto-generate key if missing
            key = Fernet.generate_key().decode()
            logger.warning(
                f"ENCRYPTION_KEY not set. Generated key: {key}\n"
                "IMPORTANT: Set this in your .env file to persist encrypted data across restarts!"
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

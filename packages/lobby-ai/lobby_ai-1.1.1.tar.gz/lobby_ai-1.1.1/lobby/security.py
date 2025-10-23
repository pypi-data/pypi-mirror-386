"""
Secure storage for API keys and sensitive configuration.
Uses macOS Keychain when available, falls back to encrypted file.
"""

import base64
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# Configure logging to redact secrets
class SecretFilter(logging.Filter):
    """Filter to redact secrets from logs."""

    REDACTED = "***REDACTED***"
    SECRET_PATTERNS = [
        "api_key",
        "apikey",
        "api-key",
        "secret",
        "password",
        "token",
        "sk-",
        "key",
    ]

    def filter(self, record):
        """Redact any secrets from log messages."""
        if hasattr(record, "msg"):
            msg = str(record.msg)
            for pattern in self.SECRET_PATTERNS:
                if pattern in msg.lower():
                    # Redact anything that looks like a secret
                    import re

                    # Match common API key patterns
                    msg = re.sub(r"(sk-[a-zA-Z0-9]{20,})", self.REDACTED, msg)
                    msg = re.sub(r"([a-zA-Z0-9]{32,})", self.REDACTED, msg)
                    record.msg = msg
                    break
        return True


# Apply secret filter to root logger
logging.getLogger().addFilter(SecretFilter())


class SecureStorage:
    """Secure storage for sensitive data."""

    def __init__(self, app_name: str = "lobby"):
        """Initialize secure storage."""
        self.app_name = app_name
        self.use_keychain = sys.platform == "darwin"  # macOS
        self.config_dir = Path.home() / ".config" / app_name
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.secure_file = self.config_dir / ".secure_storage"
        self.salt_file = self.config_dir / ".salt"

    def _get_or_create_salt(self) -> bytes:
        """Get or create a salt for key derivation."""
        if self.salt_file.exists():
            return self.salt_file.read_bytes()
        else:
            salt = os.urandom(16)
            self.salt_file.write_bytes(salt)
            # Make salt file readable only by user
            os.chmod(self.salt_file, 0o600)
            return salt

    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password."""
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def store_api_key(
        self, service: str, api_key: str, password: Optional[str] = None
    ) -> bool:
        """
        Store an API key securely.

        Args:
            service: Service name (e.g., "openrouter")
            api_key: The API key to store
            password: Password for encryption (required if not using Keychain)

        Returns:
            True if successful
        """
        if self.use_keychain:
            return self._store_keychain(service, api_key)
        else:
            if not password:
                raise ValueError("Password required for encrypted storage")
            return self._store_encrypted(service, api_key, password)

    def retrieve_api_key(
        self, service: str, password: Optional[str] = None
    ) -> Optional[str]:
        """
        Retrieve an API key.

        Args:
            service: Service name
            password: Password for decryption (required if not using Keychain)

        Returns:
            API key if found, None otherwise
        """
        if self.use_keychain:
            return self._retrieve_keychain(service)
        else:
            if not password:
                return None
            return self._retrieve_encrypted(service, password)

    def delete_api_key(self, service: str, password: Optional[str] = None) -> bool:
        """
        Delete an API key.

        Args:
            service: Service name
            password: Password for decryption (required if not using Keychain)

        Returns:
            True if successful
        """
        if self.use_keychain:
            return self._delete_keychain(service)
        else:
            if not password:
                return False
            return self._delete_encrypted(service, password)

    # macOS Keychain methods
    def _store_keychain(self, service: str, api_key: str) -> bool:
        """Store in macOS Keychain."""
        try:
            import subprocess

            # Delete existing if any
            self._delete_keychain(service)

            # Add new key
            cmd = [
                "security",
                "add-generic-password",
                "-a",
                self.app_name,
                "-s",
                f"{self.app_name}_{service}",
                "-w",
                api_key,
                "-U",  # Update if exists
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Keychain storage failed: {e}")
            return False

    def _retrieve_keychain(self, service: str) -> Optional[str]:
        """Retrieve from macOS Keychain."""
        try:
            import subprocess

            cmd = [
                "security",
                "find-generic-password",
                "-a",
                self.app_name,
                "-s",
                f"{self.app_name}_{service}",
                "-w",  # Output password only
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logging.error(f"Keychain retrieval failed: {e}")
            return None

    def _delete_keychain(self, service: str) -> bool:
        """Delete from macOS Keychain."""
        try:
            import subprocess

            cmd = [
                "security",
                "delete-generic-password",
                "-a",
                self.app_name,
                "-s",
                f"{self.app_name}_{service}",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    # Encrypted file methods
    def _store_encrypted(self, service: str, api_key: str, password: str) -> bool:
        """Store in encrypted file."""
        try:
            # Load existing data
            data = self._load_encrypted_data(password)
            if data is None:
                data = {}

            # Add new key
            data[service] = api_key

            # Encrypt and save
            return self._save_encrypted_data(data, password)
        except Exception as e:
            logging.error(f"Encrypted storage failed: {e}")
            return False

    def _retrieve_encrypted(self, service: str, password: str) -> Optional[str]:
        """Retrieve from encrypted file."""
        try:
            data = self._load_encrypted_data(password)
            if data:
                return data.get(service)
            return None
        except Exception as e:
            logging.error(f"Encrypted retrieval failed: {e}")
            return None

    def _delete_encrypted(self, service: str, password: str) -> bool:
        """Delete from encrypted file."""
        try:
            data = self._load_encrypted_data(password)
            if data and service in data:
                del data[service]
                return self._save_encrypted_data(data, password)
            return False
        except Exception as e:
            logging.error(f"Encrypted deletion failed: {e}")
            return False

    def _load_encrypted_data(self, password: str) -> Optional[Dict[str, Any]]:
        """Load and decrypt data from file."""
        if not self.secure_file.exists():
            return None

        try:
            key = self._derive_key(password)
            fernet = Fernet(key)

            encrypted_data = self.secure_file.read_bytes()
            decrypted_data = fernet.decrypt(encrypted_data)

            return json.loads(decrypted_data.decode())
        except Exception as e:
            logging.error(f"Failed to decrypt data: {e}")
            return None

    def _save_encrypted_data(self, data: Dict[str, Any], password: str) -> bool:
        """Encrypt and save data to file."""
        try:
            key = self._derive_key(password)
            fernet = Fernet(key)

            json_data = json.dumps(data).encode()
            encrypted_data = fernet.encrypt(json_data)

            self.secure_file.write_bytes(encrypted_data)
            # Make file readable only by user
            os.chmod(self.secure_file, 0o600)

            return True
        except Exception as e:
            logging.error(f"Failed to encrypt data: {e}")
            return False


def get_secure_storage() -> SecureStorage:
    """Get the secure storage instance."""
    return SecureStorage()


def store_api_key_interactive(service: str, api_key: str) -> bool:
    """
    Store API key with interactive password prompt if needed.

    Args:
        service: Service name
        api_key: API key to store

    Returns:
        True if successful
    """
    storage = get_secure_storage()

    if storage.use_keychain:
        # macOS Keychain doesn't need password
        success = storage.store_api_key(service, api_key)
        if success:
            logging.info(f"API key for {service} stored in macOS Keychain")
        return success
    else:
        # Need password for encrypted storage
        from lobby.ui import password

        pwd = password("Create a password to encrypt your API keys")
        pwd_confirm = password("Confirm password")

        if pwd != pwd_confirm:
            logging.error("Passwords don't match")
            return False

        success = storage.store_api_key(service, api_key, pwd)
        if success:
            logging.info(f"API key for {service} stored in encrypted file")
        return success


def retrieve_api_key_interactive(service: str) -> Optional[str]:
    """
    Retrieve API key with interactive password prompt if needed.

    Args:
        service: Service name

    Returns:
        API key if found
    """
    storage = get_secure_storage()

    if storage.use_keychain:
        # macOS Keychain doesn't need password
        api_key = storage.retrieve_api_key(service)
        if api_key:
            logging.info(f"API key for {service} retrieved from macOS Keychain")
        return api_key
    else:
        # Need password for encrypted storage
        from lobby.ui import password

        pwd = password("Enter password to decrypt your API keys")
        api_key = storage.retrieve_api_key(service, pwd)

        if api_key:
            logging.info(f"API key for {service} retrieved from encrypted file")
        return api_key

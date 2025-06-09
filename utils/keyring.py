import keyring
from keyring.errors import KeyringError
from typing import Optional
from pydantic import SecretStr
from loguru import logger

class KeyringManager:
    def __init__(self):
        self.service_name = "addictune"
        logger.debug(f"KeyringManager initialized with service: {self.service_name}")

    def save_secret(self, key: str, value: str, identifier: str = "") -> bool:
        """
        Save a secret in the system keyring.
        
        Args:
            key: The type of secret (e.g., 'api_key', 'listen_key')
            value: The actual secret string to store
            identifier: Optional identifier (e.g., email or username)
        """
        full_key = f"{identifier}.{key}" if identifier else key
        try:
            keyring.set_password(self.service_name, full_key, value)
            logger.debug(f"🔐 Saved {key} to keyring for {identifier or 'default'}")
            return True
        except KeyringError as e:
            logger.error(f"🔐 Failed to save {key} to keyring: {str(e)}")
            return False

    def get_secret(self, key: str, identifier: str = "") -> Optional[SecretStr]:
        """
        Retrieve a secret from the system keyring.
        
        Args:
            key: The type of secret to retrieve
            identifier: Optional identifier used when saving
        """
        full_key = f"{identifier}.{key}" if identifier else key
        try:
            if (value := keyring.get_password(self.service_name, full_key)):
                return SecretStr(value)
            logger.warning(f"🔓 No {key} found in keyring for {identifier}")
            return None
        except KeyringError as e:
            logger.error(f"🔐 Failed to retrieve {key} from keyring: {str(e)}")
            return None

    def delete_secret(self, key: str, identifier: str = "") -> bool:
        """
        Delete a secret from the keyring.
        
        Args:
            key: The type of secret to delete
            identifier: Optional identifier used when saving
        """
        full_key = f"{identifier}.{key}" if identifier else key
        try:
            keyring.delete_password(self.service_name, full_key)
            logger.debug(f"🗑️ Deleted {key} from keyring for {identifier}")
            return True
        except KeyringError as e:
            logger.error(f"🔐 Failed to delete {key} from keyring: {str(e)}")
            return False
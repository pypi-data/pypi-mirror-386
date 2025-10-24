import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from constants.constants import (
    CONFIG_FILE_NAME, CONFIG_FILE_PERMISSIONS,
    ENCRYPTION_SALT, ENCRYPTION_ITERATIONS, DEFAULT_USERNAME
)

class SessionManager:
    def __init__(self):
        self.current_org = None
        self.current_user = None
        self.pat = None
        
        # Single encrypted file in user home directory
        self.encrypted_file = os.path.join(os.path.expanduser("~"), CONFIG_FILE_NAME)
        
        self.load_session()
    
    def _get_encryption_key(self):
        """Generate encryption key from username"""
        username = os.getenv('USER', os.getenv('USERNAME', DEFAULT_USERNAME))
        password = username.encode()
        salt = ENCRYPTION_SALT
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=ENCRYPTION_ITERATIONS,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _encrypt_data(self, data):
        """Encrypt data"""
        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            encrypted_data = f.encrypt(data.encode())
            return encrypted_data
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return None
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt data"""
        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return None
    
    def set_pat(self, pat):
        self.pat = pat
        self.save_session()
    
    def set_org(self, org):
        self.current_org = org
        self.save_session()
    
    def set_user(self, user):
        self.current_user = user
        self.save_session()
    
    def get_org(self):
        return self.current_org
    
    def get_user(self):
        return self.current_user
    
    def get_pat(self):
        return self.pat
    
    def save_session(self):
        """Save all data to single encrypted file"""
        config = {
            "pat": self.pat,
            "org": self.current_org,
            "user": self.current_user
        }
        
        try:
            # Convert to JSON string
            json_data = json.dumps(config)
            
            # Encrypt the entire JSON
            encrypted_data = self._encrypt_data(json_data)
            
            if encrypted_data:
                # Write encrypted data to file
                with open(self.encrypted_file, 'wb') as f:
                    f.write(encrypted_data)
                
                # Set secure file permissions
                os.chmod(self.encrypted_file, CONFIG_FILE_PERMISSIONS)
                
        except Exception as e:
            print(f"❌ Error saving encrypted config: {e}")


    def load_session(self):
        """Load all data from single encrypted file"""
        try:
            if os.path.exists(self.encrypted_file):
                # Read encrypted data
                with open(self.encrypted_file, 'rb') as f:
                    encrypted_data = f.read()
                
                # Decrypt the data
                decrypted_json = self._decrypt_data(encrypted_data)
                
                if decrypted_json:
                    # Parse JSON
                    config = json.loads(decrypted_json)
                    
                    # Set all values
                    self.pat = config.get("pat")
                    self.current_org = config.get("org")
                    self.current_user = config.get("user")
                    
        except Exception as e:
            print(f"❌ Error loading encrypted config: {e}")

    def clear_session(self):
        """Clear saved session data"""
        self.pat = None
        self.current_org = None
        self.current_user = None
        try:
            # Remove encrypted file
            if os.path.exists(self.encrypted_file):
                os.remove(self.encrypted_file)
        except Exception as e:
            print(f"❌ Error clearing config: {e}")

# Global session instance
session = SessionManager()
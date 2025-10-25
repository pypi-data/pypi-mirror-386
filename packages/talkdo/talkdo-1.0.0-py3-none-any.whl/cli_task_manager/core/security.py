"""
Security and encryption features for the CLI Task Manager.

This module provides data encryption, secure storage, and privacy
protection features for sensitive task data.
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from cli_task_manager.core.database import DatabaseManager
from cli_task_manager.core.config import Config


class SecurityManager:
    """Manages security and encryption for the CLI Task Manager."""
    
    def __init__(self, config: Config):
        """Initialize security manager."""
        self.config = config
        self.encryption_key: Optional[bytes] = None
        self.encryption_enabled = False
        self.secure_mode = False
        
        # Security settings
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        self.session_timeout = timedelta(hours=8)
        
        # Initialize security
        self._initialize_security()
    
    def _initialize_security(self) -> None:
        """Initialize security settings."""
        # Check if encryption is enabled
        self.encryption_enabled = self.config.general.metadata.get('encryption_enabled', False)
        
        if self.encryption_enabled:
            self._load_encryption_key()
    
    def enable_encryption(self, master_password: str) -> bool:
        """Enable database encryption with master password."""
        try:
            # Generate encryption key from master password
            self.encryption_key = self._derive_key_from_password(master_password)
            
            # Encrypt existing database
            self._encrypt_database()
            
            # Update configuration
            self.config.general.metadata['encryption_enabled'] = True
            self.config.general.metadata['encryption_key_hash'] = self._hash_password(master_password)
            self.config.save()
            
            self.encryption_enabled = True
            return True
        
        except Exception as e:
            print(f"Failed to enable encryption: {e}")
            return False
    
    def disable_encryption(self, master_password: str) -> bool:
        """Disable database encryption."""
        try:
            # Verify master password
            if not self._verify_master_password(master_password):
                return False
            
            # Decrypt database
            self._decrypt_database()
            
            # Update configuration
            self.config.general.metadata['encryption_enabled'] = False
            self.config.general.metadata.pop('encryption_key_hash', None)
            self.config.save()
            
            self.encryption_enabled = False
            self.encryption_key = None
            return True
        
        except Exception as e:
            print(f"Failed to disable encryption: {e}")
            return False
    
    def _derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _hash_password(self, password: str) -> str:
        """Hash password for storage."""
        salt = os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return base64.b64encode(salt + pwd_hash).decode()
    
    def _verify_master_password(self, password: str) -> bool:
        """Verify master password."""
        stored_hash = self.config.general.metadata.get('encryption_key_hash')
        if not stored_hash:
            return False
        
        try:
            decoded = base64.b64decode(stored_hash)
            salt = decoded[:16]
            stored_pwd_hash = decoded[16:]
            
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            return pwd_hash == stored_pwd_hash
        
        except Exception:
            return False
    
    def _load_encryption_key(self) -> None:
        """Load encryption key from secure storage."""
        # In a real implementation, this would load from a secure key store
        # For now, we'll generate a new key (in production, this should be stored securely)
        if not hasattr(self, '_temp_key'):
            self._temp_key = Fernet.generate_key()
        self.encryption_key = self._temp_key
    
    def _encrypt_database(self) -> None:
        """Encrypt the database file."""
        if not self.encryption_key:
            return
        
        db_path = self.config.get_database_path()
        if not db_path.exists():
            return
        
        # Create encrypted backup
        encrypted_path = db_path.with_suffix('.db.encrypted')
        
        try:
            with open(db_path, 'rb') as f:
                data = f.read()
            
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(data)
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Replace original with encrypted version
            db_path.unlink()
            encrypted_path.rename(db_path)
            
        except Exception as e:
            print(f"Database encryption failed: {e}")
    
    def _decrypt_database(self) -> None:
        """Decrypt the database file."""
        if not self.encryption_key:
            return
        
        db_path = self.config.get_database_path()
        if not db_path.exists():
            return
        
        try:
            with open(db_path, 'rb') as f:
                encrypted_data = f.read()
            
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Create decrypted backup
            decrypted_path = db_path.with_suffix('.db.decrypted')
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)
            
            # Replace encrypted with decrypted version
            db_path.unlink()
            decrypted_path.rename(db_path)
            
        except Exception as e:
            print(f"Database decryption failed: {e}")
    
    def encrypt_field(self, data: str) -> str:
        """Encrypt a single field."""
        if not self.encryption_key:
            return data
        
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception:
            return data
    
    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt a single field."""
        if not self.encryption_key:
            return encrypted_data
        
        try:
            fernet = Fernet(self.encryption_key)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            return encrypted_data
    
    def secure_delete(self, file_path: Path, passes: int = 3) -> bool:
        """Securely delete a file by overwriting it multiple times."""
        try:
            if not file_path.exists():
                return True
            
            file_size = file_path.stat().st_size
            
            with open(file_path, 'r+b') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            file_path.unlink()
            return True
        
        except Exception as e:
            print(f"Secure delete failed: {e}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(length)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for storage."""
        salt = os.urandom(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)
        return base64.b64encode(salt + hash_obj).decode()
    
    def verify_hashed_data(self, data: str, hashed_data: str) -> bool:
        """Verify hashed sensitive data."""
        try:
            decoded = base64.b64decode(hashed_data)
            salt = decoded[:16]
            stored_hash = decoded[16:]
            
            hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt, 100000)
            return hash_obj == stored_hash
        
        except Exception:
            return False
    
    def create_secure_backup(self, backup_path: Path, password: str) -> bool:
        """Create an encrypted backup of the database."""
        try:
            db_path = self.config.get_database_path()
            if not db_path.exists():
                return False
            
            # Read database
            with open(db_path, 'rb') as f:
                data = f.read()
            
            # Encrypt with password
            key = self._derive_key_from_password(password)
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data)
            
            # Write encrypted backup
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
        
        except Exception as e:
            print(f"Secure backup creation failed: {e}")
            return False
    
    def restore_secure_backup(self, backup_path: Path, password: str) -> bool:
        """Restore from an encrypted backup."""
        try:
            if not backup_path.exists():
                return False
            
            # Read encrypted backup
            with open(backup_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt with password
            key = self._derive_key_from_password(password)
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Write to database
            db_path = self.config.get_database_path()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(db_path, 'wb') as f:
                f.write(decrypted_data)
            
            return True
        
        except Exception as e:
            print(f"Secure backup restoration failed: {e}")
            return False
    
    def audit_log(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log security-related actions."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details or {},
            "user": os.getenv("USER", "unknown"),
            "hostname": os.getenv("HOSTNAME", "unknown")
        }
        
        # Write to audit log
        audit_log_path = self.config.get_log_directory() / "security_audit.log"
        with open(audit_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def check_security_status(self) -> Dict[str, Any]:
        """Check current security status."""
        return {
            "encryption_enabled": self.encryption_enabled,
            "secure_mode": self.secure_mode,
            "database_encrypted": self._is_database_encrypted(),
            "audit_logging": self._is_audit_logging_enabled(),
            "last_security_check": datetime.utcnow().isoformat()
        }
    
    def _is_database_encrypted(self) -> bool:
        """Check if database is encrypted."""
        db_path = self.config.get_database_path()
        if not db_path.exists():
            return False
        
        # Try to read as SQLite - if it fails, it might be encrypted
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.execute("SELECT 1")
            conn.close()
            return False  # Database is readable, not encrypted
        except Exception:
            return True  # Database is not readable, might be encrypted
    
    def _is_audit_logging_enabled(self) -> bool:
        """Check if audit logging is enabled."""
        return self.config.general.metadata.get('audit_logging_enabled', False)
    
    def enable_audit_logging(self) -> None:
        """Enable audit logging."""
        self.config.general.metadata['audit_logging_enabled'] = True
        self.config.save()
        self.audit_log("audit_logging_enabled")
    
    def disable_audit_logging(self) -> None:
        """Disable audit logging."""
        self.config.general.metadata['audit_logging_enabled'] = False
        self.config.save()
        self.audit_log("audit_logging_disabled")
    
    def enable_secure_mode(self) -> None:
        """Enable secure mode with additional protections."""
        self.secure_mode = True
        self.config.general.metadata['secure_mode'] = True
        self.config.save()
        self.audit_log("secure_mode_enabled")
    
    def disable_secure_mode(self) -> None:
        """Disable secure mode."""
        self.secure_mode = False
        self.config.general.metadata['secure_mode'] = False
        self.config.save()
        self.audit_log("secure_mode_disabled")
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength."""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")
        
        # Character variety checks
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Password should contain lowercase letters")
        
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Password should contain uppercase letters")
        
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Password should contain numbers")
        
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        else:
            feedback.append("Password should contain special characters")
        
        # Common password check
        common_passwords = ["password", "123456", "qwerty", "abc123", "password123"]
        if password.lower() in common_passwords:
            score -= 2
            feedback.append("Password is too common")
        
        strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
        strength = strength_levels[min(score, 4)]
        
        return {
            "score": score,
            "strength": strength,
            "feedback": feedback,
            "is_strong": score >= 4
        }
    
    def generate_secure_password(self, length: int = 16, include_symbols: bool = True) -> str:
        """Generate a secure password."""
        import string
        
        characters = string.ascii_letters + string.digits
        if include_symbols:
            characters += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        password = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Ensure password meets strength requirements
        while not self.validate_password_strength(password)["is_strong"]:
            password = ''.join(secrets.choice(characters) for _ in range(length))
        
        return password
    
    def cleanup_audit_logs(self, days: int = 90) -> None:
        """Clean up old audit logs."""
        audit_log_path = self.config.get_log_directory() / "security_audit.log"
        if not audit_log_path.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Read all log entries
        with open(audit_log_path, 'r') as f:
            lines = f.readlines()
        
        # Filter recent entries
        recent_lines = []
        for line in lines:
            try:
                entry = json.loads(line.strip())
                entry_date = datetime.fromisoformat(entry['timestamp'])
                if entry_date >= cutoff_date:
                    recent_lines.append(line)
            except Exception:
                # Skip malformed entries
                continue
        
        # Write back recent entries
        with open(audit_log_path, 'w') as f:
            f.writelines(recent_lines)

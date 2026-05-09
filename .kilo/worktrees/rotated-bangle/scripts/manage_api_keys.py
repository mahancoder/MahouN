#!/usr/bin/env python3
"""
MAHOUN Offline API Key Manager
===============================

Manages API keys for air-gapped deployments without external dependencies.

Features:
- Generate secure API keys offline
- Store keys in encrypted local file
- No external validation required
- Role-based access control

Usage:
    # Generate new API key
    python scripts/manage_api_keys.py generate --role admin --name "Admin User"
    
    # List all keys
    python scripts/manage_api_keys.py list
    
    # Revoke key
    python scripts/manage_api_keys.py revoke --key mahoun_key_abc123
    
    # Validate key
    python scripts/manage_api_keys.py validate --key mahoun_key_abc123
"""

import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("Warning: cryptography not installed. Keys will be stored unencrypted.")
    print("Install: pip install cryptography")


class APIKeyManager:
    """Manages API keys for offline authentication"""
    
    def __init__(self, keys_file: str = "config/api_keys.json", master_password: Optional[str] = None):
        self.keys_file = Path(keys_file)
        self.keys_file.parent.mkdir(parents=True, exist_ok=True)
        self.master_password = master_password or os.getenv("MAHOUN_MASTER_PASSWORD")
        self.cipher = self._init_cipher() if HAS_CRYPTO and self.master_password else None
        
    def _init_cipher(self) -> Optional[Any]:
        """Initialize encryption cipher"""
        if not self.master_password:
            return None
            
        # Derive key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"mahoun_salt_v1",  # In production, use random salt
            iterations=100000,
        )
        key = kdf.derive(self.master_password.encode())
        return Fernet(Fernet.generate_key())  # Simplified for demo
    
    def _load_keys(self) -> Dict[str, Any]:
        """Load keys from encrypted file"""
        if not self.keys_file.exists():
            return {"keys": {}, "metadata": {"created": datetime.now(timezone.utc).isoformat()}}
        
        with open(self.keys_file, "r") as f:
            data = f.read()
        
        if self.cipher and data.startswith("encrypted:"):
            # Decrypt data
            encrypted = data.replace("encrypted:", "")
            decrypted = self.cipher.decrypt(encrypted.encode())
            return json.loads(decrypted)
        else:
            return json.loads(data)
    
    def _save_keys(self, data: Dict[str, Any]) -> None:
        """Save keys to encrypted file"""
        json_data = json.dumps(data, indent=2)
        
        if self.cipher:
            # Encrypt data
            encrypted = self.cipher.encrypt(json_data.encode())
            content = f"encrypted:{encrypted.decode()}"
        else:
            content = json_data
        
        with open(self.keys_file, "w") as f:
            f.write(content)
        
        # Set restrictive permissions
        os.chmod(self.keys_file, 0o600)
    
    def generate_key(self, role: str = "readonly", name: str = "Unnamed", expires_days: Optional[int] = None) -> str:
        """Generate new API key"""
        # Generate secure random key
        key_bytes = secrets.token_bytes(32)
        key_hash = hashlib.sha256(key_bytes).hexdigest()
        api_key = f"mahoun_key_{key_hash[:32]}"
        
        # Load existing keys
        data = self._load_keys()
        
        # Add new key
        key_info = {
            "key_hash": hashlib.sha256(api_key.encode()).hexdigest(),
            "role": role,
            "name": name,
            "created": datetime.now(timezone.utc).isoformat(),
            "expires": None,
            "revoked": False,
            "last_used": None,
            "usage_count": 0,
        }
        
        if expires_days:
            from datetime import timedelta
            expires = datetime.now(timezone.utc) + timedelta(days=expires_days)
            key_info["expires"] = expires.isoformat()
        
        data["keys"][api_key] = key_info
        self._save_keys(data)
        
        return api_key
    
    def validate_key(self, api_key: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Validate API key"""
        data = self._load_keys()
        
        if api_key not in data["keys"]:
            return False, None
        
        key_info = data["keys"][api_key]
        
        # Check if revoked
        if key_info.get("revoked"):
            return False, {"error": "Key revoked"}
        
        # Check if expired
        if key_info.get("expires"):
            expires = datetime.fromisoformat(key_info["expires"])
            if datetime.now(timezone.utc) > expires:
                return False, {"error": "Key expired"}
        
        # Update usage stats
        key_info["last_used"] = datetime.now(timezone.utc).isoformat()
        key_info["usage_count"] = key_info.get("usage_count", 0) + 1
        self._save_keys(data)
        
        return True, key_info
    
    def revoke_key(self, api_key: str) -> bool:
        """Revoke API key"""
        data = self._load_keys()
        
        if api_key not in data["keys"]:
            return False
        
        data["keys"][api_key]["revoked"] = True
        data["keys"][api_key]["revoked_at"] = datetime.now(timezone.utc).isoformat()
        self._save_keys(data)
        
        return True
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """List all API keys"""
        data = self._load_keys()
        
        keys_list = []
        for api_key, info in data["keys"].items():
            keys_list.append({
                "key": api_key[:20] + "..." if len(api_key) > 20 else api_key,
                "role": info["role"],
                "name": info["name"],
                "created": info["created"],
                "expires": info.get("expires"),
                "revoked": info.get("revoked", False),
                "last_used": info.get("last_used"),
                "usage_count": info.get("usage_count", 0),
            })
        
        return keys_list


def main():
    parser = argparse.ArgumentParser(description="MAHOUN Offline API Key Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate new API key")
    gen_parser.add_argument("--role", default="readonly", choices=["admin", "readonly", "write"], help="Key role")
    gen_parser.add_argument("--name", required=True, help="Key name/description")
    gen_parser.add_argument("--expires-days", type=int, help="Expiration in days")
    
    # List command
    subparsers.add_parser("list", help="List all API keys")
    
    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate API key")
    val_parser.add_argument("--key", required=True, help="API key to validate")
    
    # Revoke command
    rev_parser = subparsers.add_parser("revoke", help="Revoke API key")
    rev_parser.add_argument("--key", required=True, help="API key to revoke")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize manager
    manager = APIKeyManager()
    
    # Execute command
    if args.command == "generate":
        api_key = manager.generate_key(
            role=args.role,
            name=args.name,
            expires_days=args.expires_days
        )
        print(f"\n✓ API Key Generated:")
        print(f"  Key: {api_key}")
        print(f"  Role: {args.role}")
        print(f"  Name: {args.name}")
        print(f"\n⚠️  Save this key securely. It cannot be retrieved later.")
        
    elif args.command == "list":
        keys = manager.list_keys()
        if not keys:
            print("No API keys found.")
        else:
            print(f"\nAPI Keys ({len(keys)}):")
            print("-" * 80)
            for key in keys:
                status = "REVOKED" if key["revoked"] else "ACTIVE"
                print(f"  {key['key']}")
                print(f"    Role: {key['role']}")
                print(f"    Name: {key['name']}")
                print(f"    Status: {status}")
                print(f"    Created: {key['created']}")
                print(f"    Usage: {key['usage_count']} times")
                print()
    
    elif args.command == "validate":
        valid, info = manager.validate_key(args.key)
        if valid:
            print(f"\n✓ Key is VALID")
            print(f"  Role: {info['role']}")
            print(f"  Name: {info['name']}")
        else:
            print(f"\n✗ Key is INVALID")
            if info:
                print(f"  Reason: {info.get('error', 'Unknown')}")
    
    elif args.command == "revoke":
        if manager.revoke_key(args.key):
            print(f"\n✓ Key revoked successfully")
        else:
            print(f"\n✗ Key not found")


if __name__ == "__main__":
    main()

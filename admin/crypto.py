import hashlib
import secrets
import bcrypt
from cryptography.fernet import Fernet
import base64
from config import JWT_SECRET


def _get_fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(JWT_SECRET.encode()).digest())
    return Fernet(key)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def encrypt_api_key(raw: str) -> str:
    return _get_fernet().encrypt(raw.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


def generate_api_key() -> tuple[str, str, str, str]:
    raw = "sk-" + secrets.token_hex(32)
    prefix = raw[:10]
    hashed = hash_api_key(raw)
    encrypted = encrypt_api_key(raw)
    return raw, prefix, hashed, encrypted


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_verification_code() -> str:
    return str(secrets.randbelow(900000) + 100000)

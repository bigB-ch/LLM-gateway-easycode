import hashlib
import secrets
import bcrypt


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    raw = "sk-" + secrets.token_hex(32)
    prefix = raw[:10]
    hashed = hash_api_key(raw)
    return raw, prefix, hashed


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_verification_code() -> str:
    return str(secrets.randbelow(900000) + 100000)

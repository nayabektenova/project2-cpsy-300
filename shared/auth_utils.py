import os
import base64
import hashlib
import hmac
import datetime as dt
import jwt  # from PyJWT

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"

# ----- password hashing -----
def hash_password(password: str) -> str:
    """Return salted hash using PBKDF2 (only hash, no plain password)."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return base64.b64encode(salt + dk).decode("ascii")


def verify_password(password: str, stored_hash: str) -> bool:
    data = base64.b64decode(stored_hash.encode("ascii"))
    salt, real_dk = data[:16], data[16:]
    new_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(real_dk, new_dk)

# ----- JWT helpers -----
def create_token(user: dict) -> str:
    now = dt.datetime.utcnow()
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "name": user["name"],
        "iat": now,
        "exp": now + dt.timedelta(days=1),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

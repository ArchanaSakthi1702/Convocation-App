# security.py
from passlib.context import CryptContext

# Create a password hashing context using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using Argon2.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against the hashed password using Argon2.
    Returns True if it matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

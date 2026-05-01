"""
auth.py — Password hashing + JWT token (no FastAPI dependency)
"""
import streamlit as st
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int) -> str:
    secret = st.secrets["SECRET_KEY"]
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode({"user_id": user_id, "exp": expire}, secret, algorithm=ALGORITHM)


def decode_token(token: str):
    """Returns user_id or None"""
    try:
        secret  = st.secrets["SECRET_KEY"]
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except JWTError:
        return None

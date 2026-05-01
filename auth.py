"""
auth.py — Password hashing + JWT token
Uses bcrypt directly (passlib not compatible with Python 3.14)
"""
import bcrypt
import streamlit as st
from jose import JWTError, jwt
from datetime import datetime, timedelta

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(user_id: int) -> str:
    secret = st.secrets["SECRET_KEY"]
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode({"user_id": user_id, "exp": expire}, secret, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        secret  = st.secrets["SECRET_KEY"]
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except JWTError:
        return None

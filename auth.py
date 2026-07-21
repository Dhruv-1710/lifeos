import bcrypt
import streamlit as st
from jose import JWTError, jwt
from datetime import datetime, timedelta
import re

ALGORITHM         = "HS256"
TOKEN_EXPIRE_DAYS = 7

# ── PASSWORD POLICY ──────────────────────────────────────
MIN_PASSWORD_LEN = 8

def validate_password(password: str) -> tuple[bool, str]:
    """Returns (valid, error_message). Empty error means valid."""
    if len(password) < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, ""

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

# ── JWT ──────────────────────────────────────────────────
def _get_secret() -> str:
    try:
        return st.secrets["SECRET_KEY"]
    except (KeyError, FileNotFoundError):
        st.error("SECRET_KEY missing from secrets.toml — add it before signing in.")
        st.stop()

def create_token(user_id: int) -> str:
    secret = _get_secret()
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"user_id": user_id, "exp": expire, "iat": datetime.utcnow()},
        secret, algorithm=ALGORITHM
    )

def decode_token(token: str):
    """Returns user_id on success, None on any failure — never raises."""
    try:
        secret  = _get_secret()
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except (JWTError, KeyError, FileNotFoundError, Exception):
        return None

# ── RATE LIMITING (in-memory, per session) ───────────────
_MAX_ATTEMPTS  = 5
_LOCKOUT_SECS  = 300  # 5 minutes

def _attempt_key(username: str) -> str:
    return f"_login_attempts_{username}"

def _lockout_key(username: str) -> str:
    return f"_lockout_until_{username}"

def check_rate_limit(username: str) -> tuple[bool, str]:
    """Returns (allowed, message). Call before attempting login."""
    lockout_until = st.session_state.get(_lockout_key(username))
    if lockout_until and datetime.utcnow() < lockout_until:
        remaining = int((lockout_until - datetime.utcnow()).total_seconds())
        return False, f"Too many failed attempts. Try again in {remaining}s."
    return True, ""

def record_failed_attempt(username: str):
    key   = _attempt_key(username)
    count = st.session_state.get(key, 0) + 1
    st.session_state[key] = count
    if count >= _MAX_ATTEMPTS:
        st.session_state[_lockout_key(username)] = datetime.utcnow() + timedelta(seconds=_LOCKOUT_SECS)
        st.session_state[key] = 0

def reset_attempts(username: str):
    st.session_state.pop(_attempt_key(username), None)
    st.session_state.pop(_lockout_key(username), None)

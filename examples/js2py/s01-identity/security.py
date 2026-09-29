"""No raw credential logging; database state is rechecked on every request."""
from datetime import UTC, datetime, timedelta
import hashlib
import logging
import re
import secrets
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import AuthSession, User

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4,
                        hash_len=32, salt_len=16, type=Type.ID)
# A real dummy hash gives unknown accounts a password verification operation too.
# This is not a claim of constant end-to-end timing or a substitute for throttling.
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))
audit = logging.getLogger("security.audit")


def utc_now() -> datetime:
    return datetime.now(UTC)


def unauthorized() -> HTTPException:
    return HTTPException(401, "Invalid or expired credentials",
                         headers={"WWW-Authenticate": "Bearer"})


def digest_token(token: str) -> str:
    # SHA-256 is suitable here because the token has 256 random bits.
    # It is NOT a password hashing method.
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def password_matches(encoded: str, password: str) -> bool:
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def login(session: Session, login_name: str, password: str, ttl: int) -> dict:
    user = session.scalar(select(User).where(User.login == login_name).with_for_update())
    encoded = user.password_hash if user and user.password_hash else DUMMY_HASH
    correct = password_matches(encoded, password)
    if not user or not user.is_active or not correct:
        audit.info("login_rejected")  # Never interpolate submitted identity or password.
        raise unauthorized()
    if hasher.check_needs_rehash(encoded):
        user.password_hash = hasher.hash(password)
    token = secrets.token_urlsafe(32)
    now = utc_now()
    session.add(AuthSession(token_digest=digest_token(token), user_id=user.id,
        auth_version=user.auth_version, issued_at=now, expires_at=now + timedelta(seconds=ttl)))
    session.flush()
    audit.info("login_accepted actor_id=%s", user.id)
    return {"access_token": token, "token_type": "bearer", "expires_in": ttl}


def authenticate(session: Session, authorization: str | None,
                 *, change_user: bool = False, change_session: bool = False) -> tuple[User, AuthSession]:
    if not authorization:
        raise unauthorized()
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not re.fullmatch(r"[A-Za-z0-9_-]{43}", parts[1]):
        raise unauthorized()
    digest = digest_token(parts[1])
    candidate = session.get(AuthSession, digest)
    if candidate is None:
        raise unauthorized()
    # Lock order is always user -> credential -> project -> task/receipt.
    user = session.scalar(select(User).where(User.id == candidate.user_id)
                          .with_for_update(read=not change_user))
    credential = session.scalar(select(AuthSession).where(AuthSession.token_digest == digest)
        .with_for_update(read=not change_session).execution_options(populate_existing=True))
    if (not user or not credential or not user.is_active or credential.revoked_at is not None
            or credential.expires_at <= utc_now() or credential.auth_version != user.auth_version):
        raise unauthorized()
    return user, credential


def change_password(session: Session, user: User, old: str, new: str) -> None:
    if not password_matches(user.password_hash or DUMMY_HASH, old):
        raise unauthorized()
    user.password_hash = hasher.hash(new)
    user.password_changed_at = utc_now()
    user.auth_version += 1
    session.flush()
    audit.info("password_changed actor_id=%s", user.id)


def provision_user(session: Session, login_name: str, password: str) -> User:
    from schemas import LoginInput, NewPassword
    LoginInput(login=login_name, password=password)
    NewPassword(password=password)
    user = session.scalar(select(User).where(User.login == login_name).with_for_update())
    if user and user.password_hash is not None:
        raise ValueError("Account already provisioned; use an explicit password recovery policy")
    if user is None:
        user = User(login=login_name, auth_version=1, is_active=False)
        session.add(user)
    else:
        user.auth_version += 1
    user.password_hash = hasher.hash(password)
    user.is_active = True
    user.password_changed_at = utc_now()
    session.flush()
    return user


def set_active(session: Session, login_name: str, active: bool) -> None:
    user = session.scalar(select(User).where(User.login == login_name).with_for_update())
    if not user or (active and not user.password_hash):
        raise ValueError("No provisioned account to update")
    user.is_active = active
    user.auth_version += 1
    session.flush()
    audit.info("account_state_changed actor_id=%s", user.id)

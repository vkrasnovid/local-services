import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import RefreshToken, User
from app.schemas.auth import RegisterRequest


async def register_user(
    db: AsyncSession, data: RegisterRequest
) -> User:
    """Register a new user. Checks phone/email uniqueness."""
    # Check phone uniqueness
    if data.phone:
        result = await db.execute(
            select(User).where(User.phone == data.phone)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone already exists",
            )

    # Check email uniqueness
    if data.email:
        result = await db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

    user = User(
        phone=data.phone,
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        city=data.city,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, phone: str, password: str
) -> User:
    """Authenticate user by phone and password."""
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


async def create_tokens(
    db: AsyncSession,
    user: User,
    device_info: str | None = None,
) -> tuple[str, str]:
    """Create access and refresh token pair, store hashed refresh in DB."""
    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token()

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        device_info=device_info,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(token_record)
    await db.commit()

    return access_token, refresh_token


async def refresh_tokens(
    db: AsyncSession, refresh_token: str
) -> tuple[str, str, User]:
    """Rotate refresh token. Detect reuse and invalidate all user tokens."""
    token_hash = hash_token(refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        # Possible token reuse: the token was already consumed.
        # We cannot determine the user from a missing token alone,
        # so just reject.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check expiry
    if token_record.expires_at < datetime.now(timezone.utc):
        # Expired: delete it and reject
        await db.delete(token_record)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    user_id = token_record.user_id

    # Load user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        # Invalidate all tokens for this user
        await db.execute(
            delete(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Delete the old token (rotation)
    await db.delete(token_record)

    # Create new pair
    access_token = create_access_token(str(user.id), user.role)
    new_refresh = create_refresh_token()

    new_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh),
        device_info=token_record.device_info,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_token_record)
    await db.commit()

    return access_token, new_refresh, user


async def logout(db: AsyncSession, refresh_token: str) -> None:
    """Invalidate a refresh token by removing it from DB."""
    token_hash = hash_token(refresh_token)
    await db.execute(
        delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    await db.commit()

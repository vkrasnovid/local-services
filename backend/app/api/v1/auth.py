import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from app.core.limiter import limiter
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.master import MasterProfile
from app.models.notification import FcmToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    FcmTokenRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    filters = []
    if data.phone:
        filters.append(User.phone == data.phone)
    if data.email:
        filters.append(User.email == data.email)

    if filters:
        result = await db.execute(select(User).where(or_(*filters)))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this phone or email already exists",
            )

    role = data.role or "client"

    user = User(
        phone=data.phone,
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        city=data.city,
        role=role,
    )
    db.add(user)
    await db.flush()

    if role == "master":
        profile = MasterProfile(user_id=user.id)
        db.add(profile)

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import or_
    filters = []
    if data.email:
        filters.append(User.email == data.email)
    if data.phone:
        filters.append(User.phone == data.phone)
    result = await db.execute(select(User).where(or_(*filters)))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(str(user.id), user.role)
    raw_refresh = create_refresh_token()

    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_record)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(data.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()

    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        await db.delete(stored)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Load user for role
    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one()

    # Delete old token (rotation)
    await db.delete(stored)

    # Create new pair
    new_access = create_access_token(str(user.id), user.role)
    new_raw_refresh = create_refresh_token()

    new_refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_raw_refresh),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_refresh_record)
    await db.commit()

    return TokenPairResponse(
        access_token=new_access,
        refresh_token=new_raw_refresh,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: LogoutRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    token_hash = hash_token(data.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored = result.scalar_one_or_none()
    if stored:
        await db.delete(stored)
        await db.commit()

    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_active_user)):
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Save file to local storage
    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "jpg"
    filename = f"avatars/{user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = f"/opt/local-services/backend/uploads/{filename}"

    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/{filename}"
    user.avatar_url = avatar_url
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"avatar_url": avatar_url}


@router.post("/switch-role", response_model=UserResponse)
async def switch_role(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only clients can switch to master role",
        )

    # Check if master profile already exists
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = MasterProfile(user_id=user.id)
        db.add(profile)

    user.role = "master"
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/fcm-token", response_model=MessageResponse)
async def save_fcm_token(
    data: FcmTokenRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Upsert: check if this user+token combo exists
    result = await db.execute(
        select(FcmToken).where(
            FcmToken.user_id == user.id,
            FcmToken.token == data.token,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.device_info = data.device_info
        db.add(existing)
    else:
        fcm = FcmToken(
            user_id=user.id,
            token=data.token,
            device_info=data.device_info,
        )
        db.add(fcm)

    await db.commit()
    return MessageResponse(message="FCM token saved")

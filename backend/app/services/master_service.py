import math
import uuid
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    MasterProfile,
    PortfolioImage,
    Review,
    Service,
    User,
)
from app.schemas.master import MasterProfileCreate, MasterProfileUpdate


async def create_master_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: MasterProfileCreate,
) -> MasterProfile:
    """Create a master profile and update user role to 'master'."""
    # Check if profile already exists
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Master profile already exists for this user",
        )

    profile = MasterProfile(
        user_id=user_id,
        description=data.description,
        category_id=data.category_id,
        district=data.district,
        work_hours=data.work_hours,
    )
    db.add(profile)

    # Update user role
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    user.role = "master"

    await db.commit()
    await db.refresh(profile)
    return profile


async def update_master_profile(
    db: AsyncSession,
    master_profile_id: uuid.UUID,
    data: MasterProfileUpdate,
) -> MasterProfile:
    """Partial update of a master profile."""
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.id == master_profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


async def get_master_detail(
    db: AsyncSession, master_id: uuid.UUID
) -> dict[str, Any]:
    """Load master profile with services, portfolio, and recent reviews."""
    result = await db.execute(
        select(MasterProfile)
        .options(
            selectinload(MasterProfile.user),
            selectinload(MasterProfile.category),
            selectinload(MasterProfile.services),
            selectinload(MasterProfile.portfolio_images),
            selectinload(MasterProfile.reviews).selectinload(Review.client),
        )
        .where(MasterProfile.id == master_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )

    active_services = [s for s in profile.services if s.is_active]
    price_from = min((s.price for s in active_services), default=None)

    # Recent reviews (last 5, visible only)
    visible_reviews = sorted(
        [r for r in profile.reviews if r.is_visible],
        key=lambda r: r.created_at,
        reverse=True,
    )[:5]

    reviews_preview = [
        {
            "id": str(r.id),
            "rating": r.rating,
            "text": r.text,
            "client": {
                "id": str(r.client.id),
                "first_name": r.client.first_name,
                "last_name": r.client.last_name,
                "avatar_url": r.client.avatar_url,
            },
            "created_at": r.created_at.isoformat(),
        }
        for r in visible_reviews
    ]

    return {
        "id": profile.id,
        "user": profile.user,
        "category": profile.category,
        "description": profile.description,
        "district": profile.district,
        "rating_avg": float(profile.rating_avg),
        "rating_count": profile.rating_count,
        "verification_status": profile.verification_status,
        "is_available": profile.is_available,
        "price_from": float(price_from) if price_from is not None else None,
        "services_count": len(active_services),
        "work_hours": profile.work_hours,
        "services": active_services,
        "portfolio": profile.portfolio_images,
        "reviews_preview": reviews_preview,
    }


async def search_masters(
    db: AsyncSession,
    filters: dict[str, Any],
) -> dict[str, Any]:
    """Search masters with filtering, sorting, and pagination."""
    page: int = filters.get("page", 1)
    page_size: int = filters.get("page_size", 20)

    # Subquery for min service price per master
    min_price_sq = (
        select(
            Service.master_id,
            func.min(Service.price).label("price_from"),
            func.count(Service.id).label("services_count"),
        )
        .where(Service.is_active == True)  # noqa: E712
        .group_by(Service.master_id)
        .subquery()
    )

    query = (
        select(
            MasterProfile,
            min_price_sq.c.price_from,
            min_price_sq.c.services_count,
        )
        .join(User, MasterProfile.user_id == User.id)
        .outerjoin(min_price_sq, MasterProfile.id == min_price_sq.c.master_id)
        .where(User.is_active == True)  # noqa: E712
        .where(MasterProfile.is_available == True)  # noqa: E712
    )

    # Apply filters
    if filters.get("category_id"):
        query = query.where(MasterProfile.category_id == filters["category_id"])

    if filters.get("city"):
        query = query.where(User.city == filters["city"])

    if filters.get("district"):
        query = query.where(MasterProfile.district == filters["district"])

    if filters.get("rating_min"):
        query = query.where(MasterProfile.rating_avg >= filters["rating_min"])

    if filters.get("price_min") is not None:
        query = query.where(min_price_sq.c.price_from >= filters["price_min"])

    if filters.get("price_max") is not None:
        query = query.where(min_price_sq.c.price_from <= filters["price_max"])

    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.where(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                MasterProfile.description.ilike(search_term),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_by = filters.get("sort_by", "rating")
    if sort_by == "price_asc":
        query = query.order_by(min_price_sq.c.price_from.asc().nullslast())
    elif sort_by == "price_desc":
        query = query.order_by(min_price_sq.c.price_from.desc().nullslast())
    elif sort_by == "reviews":
        query = query.order_by(MasterProfile.rating_count.desc())
    else:  # default: rating
        query = query.order_by(MasterProfile.rating_avg.desc())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Need to eagerly load user and category for response
    query = query.options(
        selectinload(MasterProfile.user),
        selectinload(MasterProfile.category),
    )

    result = await db.execute(query)
    rows = result.all()

    items = []
    for row in rows:
        profile = row[0]
        price_from = row[1]
        services_count = row[2] or 0
        items.append(
            {
                "id": profile.id,
                "user": profile.user,
                "category": profile.category,
                "description": profile.description,
                "district": profile.district,
                "rating_avg": float(profile.rating_avg),
                "rating_count": profile.rating_count,
                "verification_status": profile.verification_status,
                "is_available": profile.is_available,
                "price_from": float(price_from) if price_from is not None else None,
                "services_count": services_count,
            }
        )

    pages = math.ceil(total / page_size) if page_size else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


async def add_portfolio_image(
    db: AsyncSession,
    master_id: uuid.UUID,
    image_url: str,
) -> PortfolioImage:
    """Add a portfolio image. Max 10 per master."""
    # Check current count
    count_result = await db.execute(
        select(func.count(PortfolioImage.id)).where(
            PortfolioImage.master_id == master_id
        )
    )
    current_count = count_result.scalar() or 0

    if current_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 10 portfolio images allowed",
        )

    image = PortfolioImage(
        master_id=master_id,
        image_url=image_url,
        sort_order=current_count,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


async def delete_portfolio_image(
    db: AsyncSession,
    master_id: uuid.UUID,
    image_id: uuid.UUID,
) -> None:
    """Delete a portfolio image. Verifies ownership."""
    result = await db.execute(
        select(PortfolioImage).where(PortfolioImage.id == image_id)
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio image not found",
        )

    if image.master_id != master_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this image",
        )

    await db.delete(image)
    await db.commit()

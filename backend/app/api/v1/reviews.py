import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models import Booking, MasterProfile, Review, User
from app.schemas.master import UserBrief
from app.schemas.review import (
    RatingSummary,
    ReviewCreate,
    ReviewListResponse,
    ReviewReply,
    ReviewResponse,
)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ReviewResponse)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Fetch booking
    result = await db.execute(
        select(Booking).where(Booking.id == data.booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify booking is completed
    if booking.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only review completed bookings",
        )

    # Verify current user is the booking's client
    if booking.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the client can leave a review",
        )

    # Check no existing review for this booking
    existing = await db.execute(
        select(Review).where(Review.booking_id == data.booking_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this booking",
        )

    # Create review
    review = Review(
        booking_id=data.booking_id,
        client_id=current_user.id,
        master_id=booking.master_id,
        rating=data.rating,
        text=data.text,
    )
    db.add(review)
    await db.flush()

    # Recalculate master's rating
    avg_result = await db.execute(
        select(
            func.avg(Review.rating).label("avg"),
            func.count(Review.id).label("cnt"),
        ).where(
            Review.master_id == booking.master_id,
            Review.is_visible == True,
        )
    )
    row = avg_result.one()
    master_result = await db.execute(
        select(MasterProfile).where(MasterProfile.id == booking.master_id)
    )
    master = master_result.scalar_one()
    master.rating_avg = round(row.avg or 0, 2)
    master.rating_count = row.cnt or 0

    await db.commit()
    await db.refresh(review)

    # Load client relationship
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.client))
        .where(Review.id == review.id)
    )
    review = result.scalar_one()

    return ReviewResponse(
        id=review.id,
        booking_id=review.booking_id,
        client=UserBrief.model_validate(review.client),
        rating=review.rating,
        text=review.text,
        master_reply=review.master_reply,
        created_at=review.created_at,
    )


@router.get(
    "/masters/{master_id}/reviews",
    response_model=ReviewListResponse,
)
async def get_master_reviews(
    master_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Verify master exists
    master_result = await db.execute(
        select(MasterProfile).where(MasterProfile.id == master_id)
    )
    master = master_result.scalar_one_or_none()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )

    # Base filter
    base_filter = (Review.master_id == master_id) & (Review.is_visible == True)

    # Total count
    count_result = await db.execute(
        select(func.count(Review.id)).where(base_filter)
    )
    total = count_result.scalar()

    # Rating summary
    avg_result = await db.execute(
        select(
            func.coalesce(func.avg(Review.rating), 0).label("avg"),
            func.count(Review.id).label("cnt"),
        ).where(base_filter)
    )
    avg_row = avg_result.one()

    # Distribution by star
    dist_result = await db.execute(
        select(Review.rating, func.count(Review.id))
        .where(base_filter)
        .group_by(Review.rating)
    )
    distribution = {str(i): 0 for i in range(1, 6)}
    for rating_val, cnt in dist_result.all():
        distribution[str(rating_val)] = cnt

    # Fetch reviews
    offset = (page - 1) * page_size
    reviews_result = await db.execute(
        select(Review)
        .options(selectinload(Review.client))
        .where(base_filter)
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    reviews = reviews_result.scalars().all()

    items = [
        ReviewResponse(
            id=r.id,
            booking_id=r.booking_id,
            client=UserBrief.model_validate(r.client),
            rating=r.rating,
            text=r.text,
            master_reply=r.master_reply,
            created_at=r.created_at,
        )
        for r in reviews
    ]

    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
        rating_summary=RatingSummary(
            average=round(float(avg_row.avg), 2),
            count=avg_row.cnt,
            distribution=distribution,
        ),
    )


@router.post("/{review_id}/reply", response_model=ReviewResponse)
async def reply_to_review(
    review_id: UUID,
    data: ReviewReply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("master")),
):
    # Fetch review with client
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.client))
        .where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    # Verify the review is for the master's profile
    master_result = await db.execute(
        select(MasterProfile).where(
            MasterProfile.id == review.master_id,
            MasterProfile.user_id == current_user.id,
        )
    )
    if not master_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This review is not for your profile",
        )

    review.master_reply = data.text
    await db.commit()
    await db.refresh(review)

    # Re-load client
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.client))
        .where(Review.id == review.id)
    )
    review = result.scalar_one()

    return ReviewResponse(
        id=review.id,
        booking_id=review.booking_id,
        client=UserBrief.model_validate(review.client),
        rating=review.rating,
        text=review.text,
        master_reply=review.master_reply,
        created_at=review.created_at,
    )

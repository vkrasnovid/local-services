import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import require_role
from app.models import (
    Booking,
    Category,
    MasterProfile,
    Payment,
    Payout,
    Review,
    Service,
    User,
)
from app.schemas.admin import (
    AdminPayoutUpdate,
    AdminReviewUpdate,
    AdminUserUpdate,
    BookingsStats,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    DashboardStats,
    RevenueStats,
    TransactionListResponse,
    UsersStats,
    VerificationUpdate,
)
from app.schemas.master import UserBrief
from app.schemas.payment import TransactionItem

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    # Users stats
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    new_today = (
        await db.execute(
            select(func.count(User.id)).where(User.created_at >= today_start)
        )
    ).scalar()
    new_this_week = (
        await db.execute(
            select(func.count(User.id)).where(User.created_at >= week_start)
        )
    ).scalar()

    by_role_result = await db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    by_role = {role: cnt for role, cnt in by_role_result.all()}

    # Bookings stats
    total_bookings = (await db.execute(select(func.count(Booking.id)))).scalar()
    active_bookings = (
        await db.execute(
            select(func.count(Booking.id)).where(
                Booking.status.in_(["pending", "confirmed", "in_progress"])
            )
        )
    ).scalar()
    completed_this_week = (
        await db.execute(
            select(func.count(Booking.id)).where(
                Booking.status == "completed",
                Booking.updated_at >= week_start,
            )
        )
    ).scalar()
    cancelled_this_week = (
        await db.execute(
            select(func.count(Booking.id)).where(
                Booking.status == "cancelled",
                Booking.updated_at >= week_start,
            )
        )
    ).scalar()

    # Revenue stats
    total_revenue_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == "succeeded"
        )
    )
    total_revenue = float(total_revenue_result.scalar())

    week_revenue_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == "succeeded",
            Payment.paid_at >= week_start,
        )
    )
    this_week_revenue = float(week_revenue_result.scalar())

    total_fees_result = await db.execute(
        select(func.coalesce(func.sum(Payment.platform_fee), 0)).where(
            Payment.status == "succeeded"
        )
    )
    total_fees = float(total_fees_result.scalar())

    week_fees_result = await db.execute(
        select(func.coalesce(func.sum(Payment.platform_fee), 0)).where(
            Payment.status == "succeeded",
            Payment.paid_at >= week_start,
        )
    )
    week_fees = float(week_fees_result.scalar())

    # Pending counts
    pending_verifications = (
        await db.execute(
            select(func.count(MasterProfile.id)).where(
                MasterProfile.verification_status == "pending"
            )
        )
    ).scalar()

    pending_moderation = (
        await db.execute(
            select(func.count(Review.id)).where(Review.is_visible == True)
        )
    ).scalar()

    return DashboardStats(
        users=UsersStats(
            total=total_users,
            new_today=new_today,
            new_this_week=new_this_week,
            by_role=by_role,
        ),
        bookings=BookingsStats(
            total=total_bookings,
            active=active_bookings,
            completed_this_week=completed_this_week,
            cancelled_this_week=cancelled_this_week,
        ),
        revenue=RevenueStats(
            total=total_revenue,
            this_week=this_week_revenue,
            platform_fees_total=total_fees,
            platform_fees_this_week=week_fees,
        ),
        masters_pending_verification=pending_verifications,
        reviews_pending_moderation=pending_moderation,
    )


@router.get("/users")
async def list_users(
    search: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    filters = []
    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.phone.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )
    if role:
        filters.append(User.role == role)
    if is_active is not None:
        filters.append(User.is_active == is_active)

    count_result = await db.execute(
        select(func.count(User.id)).where(*filters) if filters else select(func.count(User.id))
    )
    total = count_result.scalar()

    offset = (page - 1) * page_size
    query = select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    if filters:
        query = query.where(*filters)

    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "items": [
            {
                "id": str(u.id),
                "first_name": u.first_name,
                "last_name": u.last_name,
                "phone": u.phone,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "avatar_url": u.avatar_url,
                "city": u.city,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        user.role = data.role

    await db.commit()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "avatar_url": user.avatar_url,
        "city": user.city,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/verifications")
async def list_verifications(
    verification_status: str = Query("pending"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    filters = [MasterProfile.verification_status == verification_status]

    count_result = await db.execute(
        select(func.count(MasterProfile.id)).where(*filters)
    )
    total = count_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(MasterProfile)
        .options(selectinload(MasterProfile.user))
        .where(*filters)
        .order_by(MasterProfile.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    masters = result.scalars().all()

    return {
        "items": [
            {
                "id": str(m.id),
                "user": {
                    "id": str(m.user.id),
                    "first_name": m.user.first_name,
                    "last_name": m.user.last_name,
                    "phone": m.user.phone,
                    "email": m.user.email,
                    "avatar_url": m.user.avatar_url,
                },
                "verification_status": m.verification_status,
                "verification_docs": m.verification_docs,
                "created_at": m.created_at.isoformat(),
            }
            for m in masters
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    }


@router.patch("/verifications/{master_id}")
async def update_verification(
    master_id: UUID,
    data: VerificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(MasterProfile)
        .options(selectinload(MasterProfile.user))
        .where(MasterProfile.id == master_id)
    )
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    if data.status not in ("verified", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'verified' or 'rejected'",
        )

    master.verification_status = data.status
    await db.commit()
    await db.refresh(master)

    return {
        "id": str(master.id),
        "verification_status": master.verification_status,
        "user": {
            "id": str(master.user.id),
            "first_name": master.user.first_name,
            "last_name": master.user.last_name,
        },
    }


@router.get("/reviews")
async def list_reviews(
    is_visible: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    filters = []
    if is_visible is not None:
        filters.append(Review.is_visible == is_visible)

    count_query = select(func.count(Review.id))
    if filters:
        count_query = count_query.where(*filters)
    total = (await db.execute(count_query)).scalar()

    offset = (page - 1) * page_size
    query = (
        select(Review)
        .options(
            selectinload(Review.client),
            selectinload(Review.master).selectinload(MasterProfile.user),
        )
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        query = query.where(*filters)

    result = await db.execute(query)
    reviews = result.scalars().all()

    return {
        "items": [
            {
                "id": str(r.id),
                "booking_id": str(r.booking_id),
                "rating": r.rating,
                "text": r.text,
                "master_reply": r.master_reply,
                "is_visible": r.is_visible,
                "created_at": r.created_at.isoformat(),
                "client": {
                    "id": str(r.client.id),
                    "first_name": r.client.first_name,
                    "last_name": r.client.last_name,
                },
                "master": {
                    "id": str(r.master.id),
                    "user": {
                        "id": str(r.master.user.id),
                        "first_name": r.master.user.first_name,
                        "last_name": r.master.user.last_name,
                    },
                },
            }
            for r in reviews
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    }


@router.patch("/reviews/{review_id}")
async def update_review_visibility(
    review_id: UUID,
    data: AdminReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    review.is_visible = data.is_visible
    await db.flush()

    # Recalculate master's rating (only visible reviews)
    avg_result = await db.execute(
        select(
            func.avg(Review.rating).label("avg"),
            func.count(Review.id).label("cnt"),
        ).where(
            Review.master_id == review.master_id,
            Review.is_visible == True,
        )
    )
    row = avg_result.one()

    master_result = await db.execute(
        select(MasterProfile).where(MasterProfile.id == review.master_id)
    )
    master = master_result.scalar_one()
    master.rating_avg = round(row.avg or 0, 2)
    master.rating_count = row.cnt or 0

    await db.commit()
    await db.refresh(review)

    return {
        "id": str(review.id),
        "is_visible": review.is_visible,
        "rating": review.rating,
        "text": review.text,
    }


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    transaction_status: str | None = Query(None, alias="status"),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    filters = []
    if transaction_status:
        filters.append(Payment.status == transaction_status)
    if date_from:
        filters.append(Payment.created_at >= date_from)
    if date_to:
        filters.append(Payment.created_at <= date_to)

    count_query = select(func.count(Payment.id))
    if filters:
        count_query = count_query.where(*filters)
    total = (await db.execute(count_query)).scalar()

    # Totals
    totals_query = select(
        func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
        func.coalesce(func.sum(Payment.platform_fee), 0).label("total_fees"),
        func.coalesce(func.sum(Payment.master_amount), 0).label("total_master"),
    )
    if filters:
        totals_query = totals_query.where(*filters)
    totals_result = (await db.execute(totals_query)).one()

    offset = (page - 1) * page_size
    query = (
        select(Payment)
        .options(
            selectinload(Payment.booking)
            .selectinload(Booking.service),
            selectinload(Payment.booking)
            .selectinload(Booking.client),
            selectinload(Payment.booking)
            .selectinload(Booking.master)
            .selectinload(MasterProfile.user),
        )
        .order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        query = query.where(*filters)

    result = await db.execute(query)
    payments = result.scalars().all()

    items = [
        TransactionItem(
            id=p.id,
            booking_id=p.booking_id,
            service_name=p.booking.service.name if p.booking and p.booking.service else None,
            amount=float(p.amount),
            status=p.status,
            type="payment",
            created_at=p.created_at,
        )
        for p in payments
    ]

    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
        totals={
            "total_amount": float(totals_result.total_amount),
            "total_fees": float(totals_result.total_fees),
            "total_master": float(totals_result.total_master),
        },
    )


@router.get("/payouts")
async def list_payouts(
    payout_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    filters = []
    if payout_status:
        filters.append(Payout.status == payout_status)

    count_query = select(func.count(Payout.id))
    if filters:
        count_query = count_query.where(*filters)
    total = (await db.execute(count_query)).scalar()

    offset = (page - 1) * page_size
    query = (
        select(Payout)
        .options(
            selectinload(Payout.master).selectinload(MasterProfile.user)
        )
        .order_by(Payout.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        query = query.where(*filters)

    result = await db.execute(query)
    payouts = result.scalars().all()

    return {
        "items": [
            {
                "id": str(p.id),
                "amount": float(p.amount),
                "status": p.status,
                "card_last4": p.card_last4,
                "processed_at": p.processed_at.isoformat() if p.processed_at else None,
                "created_at": p.created_at.isoformat(),
                "master": {
                    "id": str(p.master.id),
                    "user": {
                        "id": str(p.master.user.id),
                        "first_name": p.master.user.first_name,
                        "last_name": p.master.user.last_name,
                    },
                },
            }
            for p in payouts
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    }


@router.patch("/payouts/{payout_id}")
async def update_payout(
    payout_id: UUID,
    data: AdminPayoutUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(Payout)
        .options(selectinload(Payout.master))
        .where(Payout.id == payout_id)
    )
    payout = result.scalar_one_or_none()
    if not payout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payout not found",
        )

    payout.status = data.status

    if data.status == "completed":
        payout.processed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(payout)

    return {
        "id": str(payout.id),
        "amount": float(payout.amount),
        "status": payout.status,
        "card_last4": payout.card_last4,
        "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
        "created_at": payout.created_at.isoformat(),
    }


@router.post("/categories", status_code=status.HTTP_201_CREATED, response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    category = Category(
        name=data.name,
        slug=data.slug,
        icon=data.icon,
        sort_order=data.sort_order,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return CategoryResponse.model_validate(category)


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    return CategoryResponse.model_validate(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.master_profiles))
        .where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Check no active masters in category
    active_masters = await db.execute(
        select(func.count(MasterProfile.id)).where(
            MasterProfile.category_id == category_id,
            MasterProfile.is_available == True,
        )
    )
    if active_masters.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with active masters",
        )

    # Soft delete
    category.is_active = False
    await db.commit()

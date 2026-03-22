import math
import os
import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import Float, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.master import MasterProfile
from app.models.payment import Payout
from app.models.portfolio import PortfolioImage
from app.models.review import Review
from app.models.service import Service
from app.models.user import User
from app.schemas.master import (
    MasterDetail,
    MasterListItem,
    MasterProfileUpdate,
    PaginatedResponse,
    PortfolioImageResponse,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.schemas.payment import PayoutCreate

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MasterListItem])
async def list_masters(
    category_id: Optional[uuid.UUID] = None,
    city: Optional[str] = None,
    district: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    rating_min: Optional[float] = None,
    is_available: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query(None, pattern="^(rating|price_asc|price_desc|newest)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Subquery for minimum price per master
    price_sub = (
        select(
            Service.master_id,
            func.min(Service.price).label("price_from"),
            func.count(Service.id).label("services_count"),
        )
        .where(Service.is_active == True)
        .group_by(Service.master_id)
        .subquery()
    )

    query = (
        select(MasterProfile, price_sub.c.price_from, price_sub.c.services_count)
        .outerjoin(price_sub, MasterProfile.id == price_sub.c.master_id)
        .join(User, MasterProfile.user_id == User.id)
        .options(joinedload(MasterProfile.user), joinedload(MasterProfile.category))
    )

    # Apply filters
    if category_id:
        query = query.where(MasterProfile.category_id == category_id)
    if city:
        query = query.where(User.city == city)
    if district:
        query = query.where(MasterProfile.district == district)
    if rating_min is not None:
        query = query.where(MasterProfile.rating_avg >= rating_min)
    if is_available is not None:
        query = query.where(MasterProfile.is_available == is_available)
    if price_min is not None:
        query = query.where(price_sub.c.price_from >= price_min)
    if price_max is not None:
        query = query.where(price_sub.c.price_from <= price_max)
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (User.first_name.ilike(search_filter))
            | (User.last_name.ilike(search_filter))
            | (MasterProfile.description.ilike(search_filter))
        )

    # Count query
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Sorting
    if sort_by == "rating":
        query = query.order_by(MasterProfile.rating_avg.desc())
    elif sort_by == "price_asc":
        query = query.order_by(price_sub.c.price_from.asc().nullslast())
    elif sort_by == "price_desc":
        query = query.order_by(price_sub.c.price_from.desc().nullslast())
    elif sort_by == "newest":
        query = query.order_by(MasterProfile.created_at.desc())
    else:
        query = query.order_by(MasterProfile.rating_avg.desc())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.unique().all()

    items = []
    for row in rows:
        master = row[0]
        price_from = float(row[1]) if row[1] is not None else None
        services_count = row[2] or 0

        item = MasterListItem(
            id=master.id,
            user=master.user,
            category=master.category,
            description=master.description,
            district=master.district,
            rating_avg=float(master.rating_avg),
            rating_count=master.rating_count,
            verification_status=master.verification_status,
            is_available=master.is_available,
            price_from=price_from,
            services_count=services_count,
        )
        items.append(item)

    pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{master_id}", response_model=MasterDetail)
async def get_master(master_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.id == master_id)
        .options(
            joinedload(MasterProfile.user),
            joinedload(MasterProfile.category),
            selectinload(MasterProfile.services).where(Service.is_active == True),
            selectinload(MasterProfile.portfolio_images),
        )
    )
    master = result.unique().scalar_one_or_none()

    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )

    # Get recent reviews (limit 3)
    reviews_result = await db.execute(
        select(Review)
        .where(Review.master_id == master_id, Review.is_visible == True)
        .options(joinedload(Review.client))
        .order_by(Review.created_at.desc())
        .limit(3)
    )
    reviews = reviews_result.unique().scalars().all()
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
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reviews
    ]

    # Price from and services count
    services_result = await db.execute(
        select(
            func.min(Service.price).label("price_from"),
            func.count(Service.id).label("services_count"),
        ).where(Service.master_id == master_id, Service.is_active == True)
    )
    svc_row = services_result.one()
    price_from = float(svc_row.price_from) if svc_row.price_from is not None else None
    services_count = svc_row.services_count or 0

    return MasterDetail(
        id=master.id,
        user=master.user,
        category=master.category,
        description=master.description,
        district=master.district,
        rating_avg=float(master.rating_avg),
        rating_count=master.rating_count,
        verification_status=master.verification_status,
        is_available=master.is_available,
        price_from=price_from,
        services_count=services_count,
        work_hours=master.work_hours,
        services=master.services,
        portfolio=master.portfolio_images,
        reviews_preview=reviews_preview,
    )


@router.patch("/me", response_model=MasterDetail)
async def update_my_profile(
    data: MasterProfileUpdate,
    user: User = Depends(require_role("master")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.user_id == user.id)
        .options(
            joinedload(MasterProfile.user),
            joinedload(MasterProfile.category),
            selectinload(MasterProfile.services),
            selectinload(MasterProfile.portfolio_images),
        )
    )
    profile = result.unique().scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    # Reload with relationships
    result = await db.execute(
        select(MasterProfile)
        .where(MasterProfile.id == profile.id)
        .options(
            joinedload(MasterProfile.user),
            joinedload(MasterProfile.category),
            selectinload(MasterProfile.services),
            selectinload(MasterProfile.portfolio_images),
        )
    )
    profile = result.unique().scalar_one()

    services_result = await db.execute(
        select(
            func.min(Service.price).label("price_from"),
            func.count(Service.id).label("services_count"),
        ).where(Service.master_id == profile.id, Service.is_active == True)
    )
    svc_row = services_result.one()

    return MasterDetail(
        id=profile.id,
        user=profile.user,
        category=profile.category,
        description=profile.description,
        district=profile.district,
        rating_avg=float(profile.rating_avg),
        rating_count=profile.rating_count,
        verification_status=profile.verification_status,
        is_available=profile.is_available,
        price_from=float(svc_row.price_from) if svc_row.price_from else None,
        services_count=svc_row.services_count or 0,
        work_hours=profile.work_hours,
        services=profile.services,
        portfolio=profile.portfolio_images,
        reviews_preview=[],
    )


@router.post("/me/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: ServiceCreate,
    user: User = Depends(require_role("master")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    service = Service(
        master_id=profile.id,
        name=data.name,
        description=data.description,
        price=data.price,
        duration_minutes=data.duration_minutes,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.patch("/me/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: uuid.UUID,
    data: ServiceUpdate,
    user: User = Depends(require_role("master")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.master_id == profile.id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)

    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/me/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: uuid.UUID,
    user: User = Depends(require_role("master")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    result = await db.execute(
        select(Service).where(Service.id == service_id, Service.master_id == profile.id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    service.is_active = False
    db.add(service)
    await db.commit()


@router.post("/me/portfolio", response_model=PortfolioImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_portfolio_image(
    file: UploadFile = File(...),
    user: User = Depends(require_role("master")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    # Check max 10 images
    count_result = await db.execute(
        select(func.count(PortfolioImage.id)).where(
            PortfolioImage.master_id == profile.id
        )
    )
    count = count_result.scalar() or 0
    if count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 portfolio images allowed",
        )

    # Save file
    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "jpg"
    filename = f"portfolio/{profile.id}_{uuid.uuid4().hex[:8]}.{ext}"
    file_path = f"/opt/local-services/backend/uploads/{filename}"

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    image_url = f"/uploads/{filename}"
    portfolio_image = PortfolioImage(
        master_id=profile.id,
        image_url=image_url,
        sort_order=count,
    )
    db.add(portfolio_image)
    await db.commit()
    await db.refresh(portfolio_image)
    return portfolio_image


@router.delete("/me/portfolio/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_image(
    image_id: uuid.UUID,
    user: User = Depends(require_role("master")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    result = await db.execute(
        select(PortfolioImage).where(
            PortfolioImage.id == image_id,
            PortfolioImage.master_id == profile.id,
        )
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio image not found",
        )

    await db.delete(image)
    await db.commit()


@router.get("/me/balance")
async def get_balance(
    user: User = Depends(require_role("master")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    # Total earned: sum of completed payouts
    earned_result = await db.execute(
        select(func.coalesce(func.sum(Payout.amount), 0)).where(
            Payout.master_id == profile.id,
            Payout.status == "completed",
        )
    )
    total_earned = float(earned_result.scalar())

    # Total withdrawn: sum of all payouts (completed)
    total_withdrawn = total_earned

    # Recent payouts
    payouts_result = await db.execute(
        select(Payout)
        .where(Payout.master_id == profile.id)
        .order_by(Payout.created_at.desc())
        .limit(10)
    )
    recent_payouts = payouts_result.scalars().all()

    return {
        "balance": float(profile.balance),
        "total_earned": total_earned,
        "total_withdrawn": total_withdrawn,
        "recent_payouts": [
            {
                "id": str(p.id),
                "amount": float(p.amount),
                "status": p.status,
                "card_last4": p.card_last4,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "processed_at": p.processed_at.isoformat() if p.processed_at else None,
            }
            for p in recent_payouts
        ],
    }


@router.post("/me/payout", status_code=status.HTTP_201_CREATED)
async def create_payout(
    data: PayoutCreate,
    user: User = Depends(require_role("master")),
    db: AsyncSession = Depends(get_db),
):
    amount = data.amount
    card_last4 = data.card_last4

    if not amount or amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payout amount",
        )

    result = await db.execute(
        select(MasterProfile).where(MasterProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master profile not found",
        )

    if float(profile.balance) < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance",
        )

    payout = Payout(
        master_id=profile.id,
        amount=Decimal(str(amount)),
        status="pending",
        card_last4=card_last4,
    )
    db.add(payout)

    profile.balance = profile.balance - Decimal(str(data.amount))
    db.add(profile)

    await db.commit()
    await db.refresh(payout)

    return {
        "id": str(payout.id),
        "amount": float(payout.amount),
        "status": payout.status,
        "card_last4": payout.card_last4,
        "created_at": payout.created_at.isoformat() if payout.created_at else None,
    }

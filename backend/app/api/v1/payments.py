import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models import Booking, MasterProfile, Payment, User
from app.schemas.payment import PaymentResponse, TransactionItem, WebhookPayload

router = APIRouter()


@router.get("/{booking_id}", response_model=PaymentResponse)
async def get_payment(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Fetch booking to verify participant
    booking_result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.master))
        .where(Booking.id == booking_id)
    )
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Check user is participant (client or master's user)
    is_client = booking.client_id == current_user.id
    is_master = booking.master.user_id == current_user.id
    if not is_client and not is_master:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this booking",
        )

    # Get payment
    payment_result = await db.execute(
        select(Payment).where(Payment.booking_id == booking_id)
    )
    payment = payment_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return PaymentResponse.model_validate(payment)


@router.post("/webhook")
async def payment_webhook(
    payload: WebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    payment_data = payload.object
    yukassa_id = payment_data.get("id")

    if not yukassa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payment id in webhook payload",
        )

    result = await db.execute(
        select(Payment).where(Payment.yukassa_payment_id == yukassa_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        # Payment not found, but return ok to avoid retries
        return {"status": "ok"}

    event = payload.event
    if event == "payment.succeeded":
        payment.status = "succeeded"
        payment.paid_at = datetime.now(timezone.utc)
    elif event == "payment.canceled" or event == "payment.cancelled":
        payment.status = "cancelled"
    elif event == "refund.succeeded":
        payment.status = "refunded"
        payment.refunded_at = datetime.now(timezone.utc)
    else:
        # Update status from event type
        status_str = event.split(".")[-1] if "." in event else event
        payment.status = status_str

    await db.commit()

    return {"status": "ok"}


@router.get("/transactions", response_model=None)
async def list_user_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Get master profile id if user is a master
    master_profile_id = None
    if current_user.role == "master":
        from app.models import MasterProfile
        mp_result = await db.execute(
            select(MasterProfile.id).where(
                MasterProfile.user_id == current_user.id
            )
        )
        mp_id = mp_result.scalar_one_or_none()
        if mp_id:
            master_profile_id = mp_id

    # Build filter: payments for bookings where user is client or master
    booking_subquery = (
        select(Booking.id)
        .where(
            or_(
                Booking.client_id == current_user.id,
                Booking.master_id == master_profile_id,
            )
            if master_profile_id
            else (Booking.client_id == current_user.id)
        )
    ).subquery()

    filters = [Payment.booking_id.in_(select(booking_subquery))]

    count_result = await db.execute(
        select(func.count(Payment.id)).where(*filters)
    )
    total = count_result.scalar()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Payment)
        .options(
            selectinload(Payment.booking).selectinload(Booking.service),
        )
        .where(*filters)
        .order_by(Payment.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
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

    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
    }

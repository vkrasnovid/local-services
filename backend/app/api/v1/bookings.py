import math
import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.booking import Booking
from app.models.chat import ChatRoom
from app.models.master import MasterProfile
from app.models.payment import Payment
from app.models.service import Service
from app.models.time_slot import TimeSlot
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingDetail,
    BookingListItem,
    BookingResponse,
    BookingStatusUpdate,
)
from app.schemas.master import PaginatedResponse, UserBrief

router = APIRouter()

# Valid status transitions
VALID_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify service exists
    svc_result = await db.execute(
        select(Service)
        .where(Service.id == data.service_id, Service.is_active == True)
        .options(joinedload(Service.master))
    )
    service = svc_result.unique().scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    master_profile = service.master

    # Verify slot exists and is not booked
    slot_result = await db.execute(
        select(TimeSlot).where(TimeSlot.id == data.slot_id)
    )
    slot = slot_result.scalar_one_or_none()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found",
        )
    if slot.is_booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is already booked",
        )

    # Verify slot belongs to same master as service
    if slot.master_id != service.master_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot does not belong to the service's master",
        )

    # Mark slot as booked
    slot.is_booked = True
    db.add(slot)

    # Create booking with price snapshot
    booking = Booking(
        client_id=user.id,
        master_id=master_profile.id,
        service_id=service.id,
        slot_id=slot.id,
        status="pending",
        price=service.price,
        address=data.address,
        is_online=data.is_online,
    )
    db.add(booking)
    await db.flush()

    # Create chat room
    chat_room = ChatRoom(
        booking_id=booking.id,
        client_id=user.id,
        master_user_id=master_profile.user_id,
    )
    db.add(chat_room)

    # Create payment stub
    platform_fee = service.price * Decimal(str(settings.PLATFORM_FEE_PERCENT)) / Decimal("100")
    master_amount = service.price - platform_fee

    payment = Payment(
        booking_id=booking.id,
        amount=service.price,
        platform_fee=platform_fee,
        master_amount=master_amount,
        status="pending",
    )
    db.add(payment)

    await db.commit()

    # Reload booking with relationships
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking.id)
        .options(
            joinedload(Booking.service),
            joinedload(Booking.slot),
            joinedload(Booking.payment),
        )
    )
    booking = result.unique().scalar_one()
    return booking


@router.get("/", response_model=PaginatedResponse[BookingListItem])
async def list_bookings(
    role: Optional[str] = Query(None, pattern="^(client|master)$"),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Booking).options(
        joinedload(Booking.service),
        joinedload(Booking.slot),
    )

    if role == "master":
        # Get master profile
        mp_result = await db.execute(
            select(MasterProfile).where(MasterProfile.user_id == user.id)
        )
        mp = mp_result.scalar_one_or_none()
        if not mp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Master profile not found",
            )
        query = query.where(Booking.master_id == mp.id)
    elif role == "client":
        query = query.where(Booking.client_id == user.id)
    else:
        # Default: show both client and master bookings
        mp_result = await db.execute(
            select(MasterProfile).where(MasterProfile.user_id == user.id)
        )
        mp = mp_result.scalar_one_or_none()
        if mp:
            query = query.where(
                or_(Booking.client_id == user.id, Booking.master_id == mp.id)
            )
        else:
            query = query.where(Booking.client_id == user.id)

    if status_filter:
        query = query.where(Booking.status == status_filter)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    query = query.order_by(Booking.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    bookings = result.unique().scalars().all()

    # Build list items with counterparty
    items = []
    for b in bookings:
        # Determine counterparty
        if b.client_id == user.id:
            # User is client, counterparty is master's user
            mp_result = await db.execute(
                select(MasterProfile)
                .where(MasterProfile.id == b.master_id)
                .options(joinedload(MasterProfile.user))
            )
            mp = mp_result.unique().scalar_one()
            counterparty = UserBrief.model_validate(mp.user)
        else:
            # User is master, counterparty is client
            client_result = await db.execute(
                select(User).where(User.id == b.client_id)
            )
            client = client_result.scalar_one()
            counterparty = UserBrief.model_validate(client)

        items.append(
            BookingListItem(
                id=b.id,
                service=b.service,
                slot=b.slot,
                status=b.status,
                price=float(b.price) if b.price else 0,
                counterparty=counterparty,
                created_at=b.created_at,
            )
        )

    pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{booking_id}", response_model=BookingDetail)
async def get_booking(
    booking_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            joinedload(Booking.service),
            joinedload(Booking.slot),
            joinedload(Booking.payment),
            joinedload(Booking.client),
            joinedload(Booking.master).joinedload(MasterProfile.user),
            joinedload(Booking.chat_room),
        )
    )
    booking = result.unique().scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Check participation
    is_client = booking.client_id == user.id
    is_master = booking.master.user_id == user.id
    if not is_client and not is_master:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this booking",
        )

    return BookingDetail(
        id=booking.id,
        client_id=booking.client_id,
        master_id=booking.master_id,
        client=booking.client,
        master=booking.master.user,
        service=booking.service,
        slot=booking.slot,
        status=booking.status,
        price=float(booking.price) if booking.price else 0,
        address=booking.address,
        is_online=booking.is_online,
        payment=booking.payment,
        chat_room_id=booking.chat_room.id if booking.chat_room else None,
        created_at=booking.created_at,
    )


@router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    booking_id: uuid.UUID,
    data: BookingStatusUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            joinedload(Booking.service),
            joinedload(Booking.slot),
            joinedload(Booking.payment),
            joinedload(Booking.master),
        )
    )
    booking = result.unique().scalar_one_or_none()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Check participation
    is_client = booking.client_id == user.id
    is_master = booking.master.user_id == user.id
    if not is_client and not is_master:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this booking",
        )

    # Validate transition
    allowed = VALID_TRANSITIONS.get(booking.status, set())
    if data.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{booking.status}' to '{data.status}'",
        )

    booking.status = data.status

    # On cancel: unbook slot
    if data.status == "cancelled":
        booking.cancel_reason = data.cancel_reason
        booking.cancelled_by = "client" if is_client else "master"

        slot_result = await db.execute(
            select(TimeSlot).where(TimeSlot.id == booking.slot_id)
        )
        slot = slot_result.scalar_one_or_none()
        if slot:
            slot.is_booked = False
            db.add(slot)

    # On complete: stub capture payment
    if data.status == "completed":
        if booking.payment:
            booking.payment.status = "captured"
            db.add(booking.payment)

    db.add(booking)
    await db.commit()

    # Reload
    result = await db.execute(
        select(Booking)
        .where(Booking.id == booking.id)
        .options(
            joinedload(Booking.service),
            joinedload(Booking.slot),
            joinedload(Booking.payment),
        )
    )
    booking = result.unique().scalar_one()
    return booking

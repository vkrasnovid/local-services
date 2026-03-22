import uuid
from datetime import date, time, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.master import MasterProfile
from app.models.time_slot import TimeSlot
from app.models.user import User
from app.schemas.booking import (
    BulkSlotCreate,
    BulkSlotResponse,
    TimeSlotResponse,
)

router = APIRouter()


@router.get("/masters/{master_id}/slots", response_model=list[TimeSlotResponse])
async def get_master_slots(
    master_id: uuid.UUID,
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TimeSlot)
        .where(
            TimeSlot.master_id == master_id,
            TimeSlot.date >= date_from,
            TimeSlot.date <= date_to,
        )
        .order_by(TimeSlot.date, TimeSlot.start_time)
    )
    slots = result.scalars().all()
    return slots


@router.post("/me/slots", response_model=BulkSlotResponse, status_code=status.HTTP_201_CREATED)
async def create_slots(
    data: BulkSlotCreate,
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

    created_slots = []
    for slot_data in data.slots:
        start = time.fromisoformat(slot_data.start_time)
        end = time.fromisoformat(slot_data.end_time)

        # Check for conflicts
        conflict_result = await db.execute(
            select(TimeSlot).where(
                TimeSlot.master_id == profile.id,
                TimeSlot.date == slot_data.date,
                TimeSlot.start_time < end,
                TimeSlot.end_time > start,
            )
        )
        conflict = conflict_result.scalar_one_or_none()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slot conflict on {slot_data.date} at {slot_data.start_time}-{slot_data.end_time}",
            )

        slot = TimeSlot(
            master_id=profile.id,
            date=slot_data.date,
            start_time=start,
            end_time=end,
        )
        db.add(slot)
        created_slots.append(slot)

    await db.commit()
    for s in created_slots:
        await db.refresh(s)

    return BulkSlotResponse(
        created=len(created_slots),
        items=created_slots,
    )


@router.delete("/me/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    slot_id: uuid.UUID,
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
        select(TimeSlot).where(
            TimeSlot.id == slot_id,
            TimeSlot.master_id == profile.id,
        )
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found",
        )

    if slot.is_booked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a booked time slot",
        )

    await db.delete(slot)
    await db.commit()

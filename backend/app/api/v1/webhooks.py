import ipaddress
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models.booking import Booking
from app.models.master import MasterProfile
from app.models.payment import Payment
from app.schemas.payment import WebhookPayload
from app.services import payment_service

logger = logging.getLogger(__name__)

router = APIRouter()

# YuKassa webhook IP whitelist
# https://yookassa.ru/developers/using-api/webhooks
YUKASSA_IP_NETWORKS = [
    ipaddress.ip_network("185.71.76.0/27"),
    ipaddress.ip_network("185.71.77.0/27"),
    ipaddress.ip_network("77.75.153.0/25"),
    ipaddress.ip_network("77.75.156.11/32"),
]


def _is_trusted_ip(client_ip: str) -> bool:
    """Check if the request comes from a trusted YuKassa IP."""
    try:
        addr = ipaddress.ip_address(client_ip)
        return any(addr in network for network in YUKASSA_IP_NETWORKS)
    except ValueError:
        return False


@router.post("/yukassa")
async def yukassa_webhook(
    request: Request,
    payload: WebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    # Verify source IP from actual socket connection (never trust X-Forwarded-For)
    client_ip = request.client.host if request.client else None

    if client_ip and not _is_trusted_ip(client_ip):
        logger.warning("Webhook request from untrusted IP: %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Untrusted source IP",
        )

    payment_data = payload.object
    yukassa_id = payment_data.get("id")

    if not yukassa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payment id in webhook payload",
        )

    # Find payment by yukassa_payment_id
    result = await db.execute(
        select(Payment)
        .where(Payment.yukassa_payment_id == yukassa_id)
        .options(joinedload(Payment.booking))
    )
    payment = result.unique().scalar_one_or_none()
    if not payment:
        logger.warning("Webhook for unknown yukassa payment: %s", yukassa_id)
        return {"status": "ok"}

    event = payload.event

    if event == "payment.waiting_for_capture":
        payment.status = "waiting_for_capture"
        logger.info("Payment %s waiting for capture", yukassa_id)

    elif event == "payment.succeeded":
        payment.status = "succeeded"
        payment.paid_at = datetime.now(timezone.utc)

        # Update booking status but do NOT credit master balance here.
        # Balance is credited only when booking is completed (via booking status update).
        if payment.booking:
            booking = payment.booking
            booking.status = "confirmed" if booking.status == "pending" else booking.status

        logger.info("Payment %s succeeded, booking updated", yukassa_id)

    elif event in ("payment.canceled", "payment.cancelled"):
        payment.status = "cancelled"

        # Update booking status if still pending
        if payment.booking and payment.booking.status == "pending":
            payment.booking.status = "cancelled"
            payment.booking.cancelled_by = "system"
            payment.booking.cancel_reason = "Payment cancelled"

        logger.info("Payment %s cancelled", yukassa_id)

    elif event == "refund.succeeded":
        payment.status = "refunded"
        payment.refunded_at = datetime.now(timezone.utc)
        logger.info("Refund for payment %s succeeded", yukassa_id)

    else:
        # Store unknown events but don't fail
        logger.info("Unhandled webhook event: %s for payment %s", event, yukassa_id)

    payment.metadata_ = {
        **(payment.metadata_ or {}),
        f"webhook_{event}": {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "data": payment_data,
        },
    }

    db.add(payment)
    await db.commit()

    return {"status": "ok"}

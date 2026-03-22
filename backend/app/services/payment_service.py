import logging
import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Configuration, Payment as YooPayment, Refund

from app.core.config import settings
from app.models.payment import Payment

logger = logging.getLogger(__name__)

# Configure YuKassa SDK
Configuration.account_id = settings.YUKASSA_SHOP_ID
Configuration.secret_key = settings.YUKASSA_SECRET_KEY


async def create_payment(
    db: AsyncSession,
    booking_id: uuid.UUID,
    amount: Decimal,
    description: str,
    return_url: str | None = None,
) -> dict:
    """Create a YuKassa payment with capture=False (hold).

    Returns dict with payment_id, confirmation_url, status.
    """
    idempotence_key = str(uuid.uuid4())
    rub_amount = str(amount.quantize(Decimal("0.01")))

    payment_data = {
        "amount": {
            "value": rub_amount,
            "currency": "RUB",
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url or settings.YUKASSA_RETURN_URL,
        },
        "capture": False,
        "description": description,
        "metadata": {
            "booking_id": str(booking_id),
        },
    }

    yoo_payment = YooPayment.create(payment_data, idempotence_key)

    # Update the payment record in DB with yukassa_payment_id
    result = await db.execute(
        select(Payment).where(Payment.booking_id == booking_id)
    )
    payment = result.scalar_one_or_none()
    if payment:
        payment.yukassa_payment_id = yoo_payment.id
        payment.status = yoo_payment.status  # "pending" or "waiting_for_capture"
        payment.metadata_ = {
            "yukassa_response": {
                "id": yoo_payment.id,
                "status": yoo_payment.status,
                "created_at": str(yoo_payment.created_at),
            }
        }
        db.add(payment)
        await db.flush()

    confirmation_url = None
    if yoo_payment.confirmation:
        confirmation_url = yoo_payment.confirmation.confirmation_url

    return {
        "payment_id": payment.id if payment else None,
        "confirmation_url": confirmation_url,
        "status": yoo_payment.status,
    }


async def capture_payment(db: AsyncSession, payment_id: uuid.UUID) -> bool:
    """Capture a held payment when booking is completed."""
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment or not payment.yukassa_payment_id:
        logger.warning("Payment %s not found or missing yukassa_payment_id", payment_id)
        return False

    try:
        idempotence_key = str(uuid.uuid4())
        capture_data = {
            "amount": {
                "value": str(payment.amount.quantize(Decimal("0.01"))),
                "currency": "RUB",
            },
        }
        yoo_response = YooPayment.capture(
            payment.yukassa_payment_id,
            capture_data,
            idempotence_key,
        )
        payment.status = yoo_response.status
        if yoo_response.status == "succeeded":
            payment.paid_at = datetime.now(timezone.utc)
        db.add(payment)
        await db.flush()
        return yoo_response.status == "succeeded"
    except Exception:
        logger.exception("Failed to capture payment %s", payment_id)
        return False


async def cancel_payment(db: AsyncSession, payment_id: uuid.UUID) -> bool:
    """Cancel a held payment when booking is cancelled."""
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment or not payment.yukassa_payment_id:
        logger.warning("Payment %s not found or missing yukassa_payment_id", payment_id)
        return False

    try:
        idempotence_key = str(uuid.uuid4())
        yoo_response = YooPayment.cancel(
            payment.yukassa_payment_id,
            idempotence_key,
        )
        payment.status = yoo_response.status
        db.add(payment)
        await db.flush()
        return yoo_response.status == "canceled"
    except Exception:
        logger.exception("Failed to cancel payment %s", payment_id)
        return False


async def refund_payment(db: AsyncSession, payment_id: uuid.UUID) -> bool:
    """Refund a captured (succeeded) payment."""
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment or not payment.yukassa_payment_id:
        logger.warning("Payment %s not found or missing yukassa_payment_id", payment_id)
        return False

    if payment.status != "succeeded":
        logger.warning("Cannot refund payment %s with status %s", payment_id, payment.status)
        return False

    try:
        idempotence_key = str(uuid.uuid4())
        refund_data = {
            "payment_id": payment.yukassa_payment_id,
            "amount": {
                "value": str(payment.amount.quantize(Decimal("0.01"))),
                "currency": "RUB",
            },
        }
        refund_response = Refund.create(refund_data, idempotence_key)
        if refund_response.status == "succeeded":
            payment.status = "refunded"
            payment.refunded_at = datetime.now(timezone.utc)
        else:
            # Refund is pending, will be confirmed via webhook
            payment.status = "refund_pending"
        db.add(payment)
        await db.flush()
        return True
    except Exception:
        logger.exception("Failed to refund payment %s", payment_id)
        return False


async def get_payment_status(db: AsyncSession, payment_id: uuid.UUID) -> str | None:
    """Check payment status from YuKassa API and sync to DB."""
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment or not payment.yukassa_payment_id:
        return None

    try:
        yoo_payment = YooPayment.find_one(payment.yukassa_payment_id)
        if yoo_payment.status != payment.status:
            payment.status = yoo_payment.status
            if yoo_payment.status == "succeeded" and not payment.paid_at:
                payment.paid_at = datetime.now(timezone.utc)
            db.add(payment)
            await db.flush()
        return yoo_payment.status
    except Exception:
        logger.exception("Failed to get payment status for %s", payment_id)
        return payment.status

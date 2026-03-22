from celery import Celery

from app.core.config import settings

celery = Celery(
    "local_services",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # "send-booking-reminders": {
        #     "task": "app.tasks.reminders.send_booking_reminders",
        #     "schedule": 900.0,  # every 15 minutes
        # },
    },
)

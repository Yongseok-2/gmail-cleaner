from fastapi import APIRouter

from app.models.email import EmailSyncRequest, EmailSyncResponse
from app.services.gmail import gmail_service
from app.services.kafka_producer import kafka_email_producer

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/sync", response_model=EmailSyncResponse)
async def sync_unread_emails(payload: EmailSyncRequest) -> EmailSyncResponse:
    unread_emails = await gmail_service.fetch_unread_emails(
        access_token=payload.access_token,
        user_id=payload.user_id,
        max_results=payload.max_results,
    )

    published_count = 0
    for email in unread_emails:
        await kafka_email_producer.publish_email(email)
        published_count += 1

    return EmailSyncResponse(
        fetched_count=len(unread_emails),
        published_count=published_count,
        topic=kafka_email_producer.topic,
    )

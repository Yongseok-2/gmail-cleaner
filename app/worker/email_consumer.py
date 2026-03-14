import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import asyncpg
from aiokafka import AIOKafkaConsumer

from app.core.settings import settings

INSERT_SQL = """
INSERT INTO emails_raw (
    gmail_message_id,
    gmail_thread_id,
    subject,
    from_email,
    to_email,
    date_header,
    snippet,
    internal_date,
    label_ids,
    payload_json,
    processed_at
)
VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb, $11
)
ON CONFLICT (gmail_message_id)
DO UPDATE SET
    gmail_thread_id = EXCLUDED.gmail_thread_id,
    subject = EXCLUDED.subject,
    from_email = EXCLUDED.from_email,
    to_email = EXCLUDED.to_email,
    date_header = EXCLUDED.date_header,
    snippet = EXCLUDED.snippet,
    internal_date = EXCLUDED.internal_date,
    label_ids = EXCLUDED.label_ids,
    payload_json = EXCLUDED.payload_json,
    processed_at = EXCLUDED.processed_at;
"""


async def save_email(pool: asyncpg.Pool, email: dict[str, Any]) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            INSERT_SQL,
            email.get("gmail_message_id"),
            email.get("gmail_thread_id"),
            email.get("subject"),
            email.get("from_email"),
            email.get("to_email"),
            email.get("date_header"),
            email.get("snippet"),
            email.get("internal_date"),
            json.dumps(email.get("label_ids", [])),
            json.dumps(email.get("raw", {})),
            datetime.now(UTC),
        )


async def run_consumer() -> None:
    pool = await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=1, max_size=5)
    consumer = AIOKafkaConsumer(
        settings.email_raw_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )
    await consumer.start()
    try:
        async for msg in consumer:
            email_payload = msg.value
            await save_email(pool, email_payload)
    finally:
        await consumer.stop()
        await pool.close()


if __name__ == "__main__":
    asyncio.run(run_consumer())

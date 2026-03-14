import json
from typing import Any

from aiokafka import AIOKafkaProducer
from fastapi import HTTPException, status

from app.core.settings import settings


class KafkaEmailProducer:
    def __init__(self) -> None:
        self.topic = settings.email_raw_topic
        self._started = False
        self.producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        if self._started:
            return
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        await self.producer.start()
        self._started = True

    async def stop(self) -> None:
        if not self._started or self.producer is None:
            return
        await self.producer.stop()
        self.producer = None
        self._started = False

    async def publish_email(self, email_payload: dict[str, Any]) -> None:
        if not self._started or self.producer is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kafka producer is not ready",
            )
        await self.producer.send_and_wait(self.topic, email_payload)


kafka_email_producer = KafkaEmailProducer()

import json
from typing import Any

from aiokafka import AIOKafkaProducer
from fastapi import HTTPException, status

from app.core.settings import settings


class KafkaEmailProducer:
    """이메일 payload를 Kafka로 전송하는 비동기 producer."""

    def __init__(self) -> None:
        """Kafka producer의 기본 설정값을 초기화한다."""
        self.topic = settings.email_raw_topic
        self._started = False
        self.producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """producer를 시작하고 전송 가능한 상태로 만든다."""
        if self._started:
            return
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        await self.producer.start()
        self._started = True

    async def stop(self) -> None:
        """producer를 안전하게 종료한다."""
        if not self._started or self.producer is None:
            return
        await self.producer.stop()
        self.producer = None
        self._started = False

    async def publish_email(self, email_payload: dict[str, Any]) -> None:
        """이메일 데이터를 지정된 Kafka 토픽으로 발행한다."""
        if not self._started or self.producer is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Kafka producer is not ready",
            )
        await self.producer.send_and_wait(self.topic, email_payload)


kafka_email_producer = KafkaEmailProducer()

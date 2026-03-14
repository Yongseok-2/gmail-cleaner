from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.auth import router as auth_router
from app.api.email import router as email_router
from app.services.kafka_producer import kafka_email_producer


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await kafka_email_producer.start()
    except Exception:
        # Keep API available for auth endpoints even when Kafka is unavailable.
        pass
    try:
        yield
    finally:
        await kafka_email_producer.stop()


app = FastAPI(title="InboxZero AI API", version="0.3.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(email_router)
app.include_router(analysis_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

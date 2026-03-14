from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.email import router as email_router
from app.core.settings import settings
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


app = FastAPI(title="InboxZero AI API", version="0.2.0", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(email_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)

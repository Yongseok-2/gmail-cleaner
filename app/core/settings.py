import os


class Settings:
    port: int = int(os.getenv("PORT", "8888"))
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    email_raw_topic: str = os.getenv("EMAIL_RAW_TOPIC", "email-raw")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "inboxzero-email-workers")
    postgres_dsn: str = os.getenv(
        "POSTGRES_DSN",
        "postgresql://inboxzero:inboxzero@localhost:5432/inboxzero",
    )
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    gemini_timeout_seconds: int = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "20"))
    analysis_confidence_threshold: float = float(
        os.getenv("ANALYSIS_CONFIDENCE_THRESHOLD", "0.72")
    )


settings = Settings()

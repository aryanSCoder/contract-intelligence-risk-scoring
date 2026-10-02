import os


class Settings:
    APP_NAME = os.getenv(
        "APP_NAME",
        "AI Contract Intelligence & Risk Scoring"
    )
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
ROOT = Path(__file__).resolve().parent
class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-this-local-development-key")
    DEBUG = os.getenv("APP_ENV", "development") == "development"
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(ROOT / "data" / "technology_news.db"))
    TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Karachi")
    COLLECTION_INTERVAL_HOURS = int(os.getenv("COLLECTION_INTERVAL_HOURS", "3"))
    DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "8"))
    MAX_DIGEST_ARTICLES = int(os.getenv("MAX_DIGEST_ARTICLES", "10"))
    MIN_DIGEST_SCORE = int(os.getenv("MIN_DIGEST_SCORE", "50"))
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    NEWS_API_QUERY = os.getenv("NEWS_API_QUERY", "artificial intelligence OR technology OR cybersecurity OR robotics OR cloud computing OR semiconductors")
    NEWS_API_LANGUAGE = os.getenv("NEWS_API_LANGUAGE", "en")
    NEWS_API_PAGE_SIZE = min(100, max(1, int(os.getenv("NEWS_API_PAGE_SIZE", "100"))))
    AI_PROVIDER = os.getenv("AI_PROVIDER", "")
    AI_MODEL = os.getenv("AI_MODEL", "")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MAX_CALLS_PER_RUN = int(os.getenv("AI_MAX_CALLS_PER_RUN", "50"))
    AI_MAX_INPUT_CHARS = int(os.getenv("AI_MAX_INPUT_CHARS", "4500"))
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    DIGEST_FROM_EMAIL = os.getenv("DIGEST_FROM_EMAIL", "")
    DIGEST_TO_EMAIL = os.getenv("DIGEST_TO_EMAIL", "")

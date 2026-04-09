import os
from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        # Fallback to SQLite for quick local dev if needed
        f"sqlite:///{os.path.join(os.getcwd(), 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email notifications via Formsubmit
    FORMSUBMIT_ENABLED = os.getenv("FORMSUBMIT_ENABLED", "0") in ("1", "true", "True")
    FORMSUBMIT_PER_USER = os.getenv("FORMSUBMIT_PER_USER", "0") in ("1", "true", "True")
    FORMSUBMIT_RECIPIENT = os.getenv("FORMSUBMIT_RECIPIENT")  # aggregator email (if PER_USER disabled)
    FORMSUBMIT_FROM = os.getenv("FORMSUBMIT_FROM", "no-reply@asto.local")
    FORMSUBMIT_SENDER_NAME = os.getenv("FORMSUBMIT_SENDER_NAME", "ASTO Notifications")
    FORMSUBMIT_SUBJECT_PREFIX = os.getenv("FORMSUBMIT_SUBJECT_PREFIX", "[ASTO]")

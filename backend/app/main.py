from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.v1.detect_scam import router as detect_scam_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app import models

settings = get_settings()
Base.metadata.create_all(bind=engine)

def ensure_user_oauth_columns() -> None:
    inspector = inspect(engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))
        if "phone_number" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(40)"))
        if "normalized_phone_number" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN normalized_phone_number VARCHAR(40)"))
        if "google_sub" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN google_sub VARCHAR(255)"))
        if "auth_provider" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(30) DEFAULT 'local' NOT NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_number ON users (phone_number)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_normalized_phone_number ON users (normalized_phone_number)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub ON users (google_sub)"))


def ensure_notification_and_contact_columns() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    with engine.begin() as connection:
        if "notifications" in table_names:
            notification_columns = {column["name"] for column in inspector.get_columns("notifications")}
            if "target_email" not in notification_columns:
                connection.execute(text("ALTER TABLE notifications ADD COLUMN target_email VARCHAR(255)"))
        if "trusted_contacts" in table_names:
            trusted_contact_columns = {column["name"] for column in inspector.get_columns("trusted_contacts")}
            if "phone_number" not in trusted_contact_columns:
                connection.execute(text("ALTER TABLE trusted_contacts ADD COLUMN phone_number VARCHAR(40)"))
            if "status" not in trusted_contact_columns:
                connection.execute(text("ALTER TABLE trusted_contacts ADD COLUMN status VARCHAR(30) DEFAULT 'pending' NOT NULL"))
            if "confirmation_token" not in trusted_contact_columns:
                connection.execute(text("ALTER TABLE trusted_contacts ADD COLUMN confirmation_token VARCHAR(255)"))
            if "confirmed_at" not in trusted_contact_columns:
                connection.execute(text("ALTER TABLE trusted_contacts ADD COLUMN confirmed_at TIMESTAMP"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_trusted_contacts_user_id ON trusted_contacts (user_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_trusted_contacts_email ON trusted_contacts (email)"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_trusted_contacts_confirmation_token ON trusted_contacts (confirmation_token)"))


ensure_user_oauth_columns()
ensure_notification_and_contact_columns()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = Path(settings.upload_dir)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(detect_scam_router)
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

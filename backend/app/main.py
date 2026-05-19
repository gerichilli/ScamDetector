from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

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


ensure_user_oauth_columns()

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

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

from fastapi import APIRouter

from app.api.v1 import admin, alerts, auth, history, lookup, reports, scam_database, stats, chat, trusted_contacts

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(alerts.router)
api_router.include_router(lookup.router)
api_router.include_router(reports.router)
api_router.include_router(history.router)
api_router.include_router(stats.router)
api_router.include_router(admin.router)
api_router.include_router(scam_database.router)
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(trusted_contacts.router)

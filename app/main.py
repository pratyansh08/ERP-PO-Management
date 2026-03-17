from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.router import api_router
from app.db.base import Base
from app.db.session import engine
from app.core.config import settings

# Ensure models are registered with SQLAlchemy metadata
from app import models as _models  # noqa: F401


app = FastAPI(title="Purchase Order Management System")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Purchase Order Management System API",
        "docs": "/docs",
        "api_base": "/api",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # Allows the API server (and /docs) to start even if DB is unavailable.
        # Endpoints will still fail until DATABASE_URL is reachable.
        pass


app.include_router(api_router, prefix="/api")


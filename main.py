from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import auth, groups, users
from core.config import settings
from db.session import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(
        title="API Samba AD",
        version="1.0.0",
        description="API REST para gerenciamento de Samba Active Directory via samba-tool.",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1", tags=["users"])
    app.include_router(groups.router, prefix="/api/v1", tags=["groups"])

    @app.on_event("startup")
    def _init_db() -> None:
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()

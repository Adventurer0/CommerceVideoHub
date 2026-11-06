from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from .db import ROOT, make_engine, runtime_dir
from .domain.contracts import Platform

SCHEMA_VERSION = "0001"


def create_app(data_dir: Path | None = None) -> FastAPI:
    database = (data_dir or runtime_dir()) / "app.db"
    engine = make_engine(database)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    application = FastAPI(title="CommerceVideoHub", version="0.1.0", lifespan=lifespan,
                          docs_url=None, redoc_url=None)
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @application.get("/api/health")
    def health() -> dict[str, str | bool]:
        try:
            with engine.connect() as connection:
                revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                journal = connection.execute(text("PRAGMA journal_mode")).scalar_one()
                fk = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
                if revision != SCHEMA_VERSION or journal != "wal" or fk != 1:
                    raise HTTPException(503, "Database migration or configuration required")
        except SQLAlchemyError:
            raise HTTPException(503, "Database unavailable; run start.ps1") from None
        return {"status": "ok", "stage": "G1", "database": "ok", "schema_version": SCHEMA_VERSION,
                "publishing_enabled": False}

    @application.get("/api/platforms")
    def platforms() -> list[dict[str, str]]:
        return [{"platform": p.value, "publishing": "unsupported", "verification": "manual_required"}
                for p in Platform]

    # Reserve the API namespace, including when StaticFiles is mounted at root.
    @application.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    def unavailable(path: str) -> None:
        raise HTTPException(404, "API not implemented in G1")

    dist = ROOT / "app" / "frontend" / "dist"
    if dist.is_dir():
        application.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return application


app = create_app()

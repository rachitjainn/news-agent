from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from news_agent.api.routes import router
from news_agent.config import get_settings
from news_agent.db import configure_engine, init_db
from news_agent.logging import configure_logging
from news_agent.ui.routes import router as ui_router

def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        # Keep first-run setup friction low in dev/test; production should still use alembic.
        init_db()
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(router)
    app.include_router(ui_router)

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run("news_agent.main:app", host=settings.api_host, port=settings.api_port, reload=False)

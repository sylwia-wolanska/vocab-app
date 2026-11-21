import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.courses.router import router as courses_router
from app.db.session import engine
from app.health.router import router as health_router

setup_logging(settings.debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s", settings.app_name)
    yield
    engine.dispose()
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router, prefix=settings.api_prefix)

app = FastAPI(title=settings.app_name, lifespan=lifespan)
register_exception_handlers(app)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(courses_router, prefix=settings.api_prefix)

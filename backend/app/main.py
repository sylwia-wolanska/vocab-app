import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.health.router import router as health_router

setup_logging(settings.debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router, prefix=settings.api_prefix)

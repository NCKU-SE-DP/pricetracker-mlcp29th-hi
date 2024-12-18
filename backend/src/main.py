from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk

from .config import configuration
from .crawler import exception_handlers as crawler_exception_handlers
from .database import get_database, get_database_with_auto_persist_changes_disabled
from .llm_client import exception_handlers as llm_client_exception_handlers
from .models import NewsArticle
from .news import service as news_service
from .news.router import router as news_api_router
from .price.router import router as price_api_router
from .user import exception_handlers as user_exception_handler
from .user.router import router as user_api_router


sentry_sdk.init(
    dsn=configuration.sentry_dsn,
    traces_sample_rate=configuration.sentry_traces_sample_rate,
    profiles_sample_rate=configuration.sentry_profiles_sample_rate,
)


def start_scheduler():
    database = get_database_with_auto_persist_changes_disabled()
    if database.query(NewsArticle).count() == 0:
        # TODO: should change into simple factory pattern
        news_service.download_price_changes_news(database)
    database.close()

    def job():
        database = get_database()
        news_service.download_price_changes_news(database)
        database.close()

    background_scheduler.add_job(job, "interval", minutes=100)
    background_scheduler.start()

def shutdown_scheduler():
    background_scheduler.shutdown()

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)
background_scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=configuration.cors_allow_origins,
    allow_credentials=configuration.cors_allow_credentials,
    allow_methods=configuration.cors_allow_methods,
    allow_headers=configuration.cors_allow_headers,
)


app.include_router(user_api_router)
app.include_router(news_api_router)
app.include_router(price_api_router)


crawler_exception_handlers.attach_to(app)
llm_client_exception_handlers.attach_to(app)
user_exception_handler.attach_to(app)
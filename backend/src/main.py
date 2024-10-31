import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, FastAPI
import os

from .database import get_database, get_database_with_auto_persist_changes_disabled
from .models import NewsArticle
from .user.router import router as user_api_router

from .news import service as news_service
from .news.router import router as news_api_router

from .price.router import router as price_api_router

# from pydantic import BaseModel

sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os

@app.on_event("startup")
def start_scheduler():
    database = get_database_with_auto_persist_changes_disabled()
    if database.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        news_service.download_price_changes_news()
    database.close()

    def job():
        database = get_database()
        news_service.download_price_changes_news(database)
        database.close()

    background_scheduler.add_job(job, "interval", minutes=100)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()


app.include_router(user_api_router)
app.include_router(news_api_router)
app.include_router(price_api_router)
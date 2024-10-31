import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
import os

from pydantic import BaseModel, Field, AnyHttpUrl

from .database import get_database_with_auto_persist_changes_disabled
from .dependencies import DatabaseSession
from .models import NewsArticle
from .user.dependencies import CurrentLoggedInUser
from .user.router import router as user_api_router

from .news import service as news_service

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
from openai import OpenAI


import requests
from bs4 import BeautifulSoup

@app.on_event("startup")
def start_scheduler():
    database = get_database_with_auto_persist_changes_disabled()
    if database.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        news_service.download_price_changes_news()
    database.close()
    background_scheduler.add_job(news_service.download_price_changes_news, "interval", minutes=100)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()


@app.get("/api/v1/news/news")
def read_news(database: DatabaseSession):
    """
    read news

    :param database:
    :return:
    """
    news_list = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    news_list_adding_upvote_status = []
    for news in news_list:
        upvotes, is_upvoted = news_service.get_upvote_status(news.id, None, database)
        news_list_adding_upvote_status.append(
            {**news.__dict__, "upvotes": upvotes, "is_upvoted": is_upvoted}
        )
    return news_list_adding_upvote_status


@app.get(
    "/api/v1/news/user_news"
)
def read_user_news(database: DatabaseSession, user: CurrentLoggedInUser):
    """
    read user news

    :param database:
    :param user:
    :return:
    """
    news_list = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    news_list_adding_upvote_status = []
    for news in news_list:
        upvotes, is_upvoted = news_service.get_upvote_status(news.id, user.id, database)
        news_list_adding_upvote_status.append(
            {
                **news.__dict__,
                "upvotes": upvotes,
                "is_upvoted": is_upvoted,
            }
        )
    return news_list_adding_upvote_status

class SearchRequestSchema(BaseModel):
    prompt: str

@app.post("/api/v1/news/search_news")
async def search_news(search_query: SearchRequestSchema):
    prompt = search_query.prompt
    news_list = []
    messages = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "user", "content": f"{prompt}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    keywords = completion.choices[0].message.content
    # should change into simple factory pattern
    news_snapshots = news_service.fetch_news_snapshots(keywords, is_initial=False)
    for snapshot in news_snapshots:
        try:
            response = requests.get(snapshot["titleLink"])
            soup = BeautifulSoup(response.text, "html.parser")
            # 標題
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            # 定位到包含文章内容的 <section>
            content_section = soup.find("section", class_="article-content__editor")

            paragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            news = {
                "url": snapshot["titleLink"],
                "title": title,
                "time": time,
                "content": paragraphs,
            }
            news["content"] = " ".join(news["content"])
            news["id"] = next(news_service._news_id_counter)
            news_list.append(news)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

class NewsSummaryRequestSchema(BaseModel):
    content: str

@app.post("/api/v1/news/news_summary")
async def summarize_news(
        news: NewsSummaryRequestSchema, user: CurrentLoggedInUser):
    news_summary = {}
    messages = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "user", "content": f"{news.content}"},
    ]

    completion = OpenAI(api_key="xxx").chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    content = completion.choices[0].message.content
    if content:
        content = json.loads(content)
        news_summary["summary"] = content["影響"]
        news_summary["reason"] = content["原因"]
    return news_summary


@app.post("/api/v1/news/{id}/upvote")
def upvote_news(
        id,
        database: DatabaseSession,
        user: CurrentLoggedInUser
):
    message = news_service.toggle_upvote(id, user.id, database)
    return {"message": message}




@app.get("/api/v1/prices/necessities-price")
def read_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json()

app.include_router(user_api_router)
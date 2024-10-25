import json
import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
import itertools
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker
from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException, Query, Depends, status, FastAPI
import os
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from pydantic import BaseModel, Field, AnyHttpUrl
from sqlalchemy import (Column, ForeignKey, Integer, String, Table, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


user_news_association_table = Table(
    "user_news_upvotes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column(
        "news_articles_id", Integer, ForeignKey("news_articles.id"), primary_key=True
    ),
)

# from pydantic import BaseModel


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    upvoted_news = relationship(
        "NewsArticle",
        secondary=user_news_association_table,
        back_populates="upvoted_by_users",
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    time = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    upvoted_by_users = relationship(
        "User", secondary=user_news_association_table, back_populates="upvoted_news"
    )


engine = create_engine("sqlite:///news_database.db", echo=True)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

sentry_sdk.init(
    dsn="https://4001ffe917ccb261aa0e0c34026dc343@o4505702629834752.ingest.us.sentry.io/4507694792704000",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = FastAPI()
background_scheduler = BackgroundScheduler()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from openai import OpenAI


# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content

#
# def extract_search_keywords(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key="xxx").chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=m,
#     )
#     return completion.choices[0].message.content


from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session


def save_news(news):
    """
    save news to database
    :param news:
    :return:
    """
    session = Session()
    session.add(NewsArticle(
        url=news["url"],
        title=news["title"],
        time=news["time"],
        content=" ".join(news["content"]),  # 將內容list轉換為字串
        summary=news["summary"],
        reason=news["reason"],
    ))
    session.commit()
    session.close()


def fetch_news_snapshots(search_term, is_initial=False):
    """
    fetch news snapshots

    :param search_term:
    :param is_initial:
    :return:
    """
    news_snapshots = []
    # iterate pages to get more news data, not actually get all news data
    if is_initial:
        snapshots_by_page = []
        for page in range(1, 10):
            parameters = {
                "page": page,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=parameters)
            snapshots_by_page.append(response.json()["lists"])

        for snaptshots in snapshots_by_page:
            news_snapshots.append(snaptshots)
    else:
        parameters = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=parameters)

        news_snapshots = response.json()["lists"]
    return news_snapshots

def download_price_changes_news(is_initial=False):
    """
    download price changes news

    :param is_initial:
    :return:
    """
    news_snapshots = fetch_news_snapshots("價格", is_initial=is_initial)
    for snapshot in news_snapshots:
        title = snapshot["title"]
        messages = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "user", "content": f"{title}"},
        ]
        completion = OpenAI(api_key="xxx").chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        relevance = completion.choices[0].message.content
        if relevance == "high":
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
            news =  {
                "url": snapshot["titleLink"],
                "title": title,
                "time": time,
                "content": paragraphs,
            }
            messages = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "user", "content": " ".join(news["content"])},
            ]

            completion = OpenAI(api_key="xxx").chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            summary = completion.choices[0].message.content
            summary = json.loads(summary)
            news["summary"] = summary["影響"]
            news["reason"] = summary["原因"]
            save_news(news)


@app.on_event("startup")
def start_scheduler():
    database = SessionLocal()
    if database.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        download_price_changes_news()
    database.close()
    background_scheduler.add_job(download_price_changes_news, "interval", minutes=100)
    background_scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def session_opener():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()



def is_password_correct(password, existing_password_hash):
    return password_context.verify(password, existing_password_hash)


def retrieve_user_by_credentials(database, username, password):
    user = database.query(User).filter(User.username == username).first()
    if not is_password_correct(password, user.hashed_password):
        return False
    return user


def retrieve_user_by_access_token(
    token = Depends(oauth2_scheme),
    database = Depends(session_opener)
):
    claims = jwt.decode(token, key='1892dhianiandowqd0n', algorithms=["HS256"])
    return database.query(User).filter(User.username == claims.get("sub")).first()


def create_access_token(claims, valid_duration=None):
    """create access token"""
    claims = claims.copy()
    if valid_duration:
        expiration_time = datetime.utcnow() + valid_duration
    else:
        expiration_time = datetime.utcnow() + timedelta(minutes=15)
    claims.update({"exp": expiration_time})
    print(claims)
    token = jwt.encode(claims, key='1892dhianiandowqd0n', algorithm="HS256")
    return token


@app.post("/api/v1/users/login")
async def login_for_access_token(
        form_response: OAuth2PasswordRequestForm = Depends(), database: Session = Depends(session_opener)
):
    """login"""
    user = retrieve_user_by_credentials(database, form_response.username, form_response.password)
    access_token = create_access_token(
        claims={"sub": str(user.username)}, valid_duration=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

class UserRegistrationRequestSchema(BaseModel):
    username: str
    password: str

@app.post("/api/v1/users/register")
def register_user(registration: UserRegistrationRequestSchema, database: Session = Depends(session_opener)):
    """register user"""
    hashed_password = password_context.hash(registration.password)
    new_user = User(username=registration.username, hashed_password=hashed_password)
    database.add(new_user)
    database.commit()
    database.refresh(new_user)
    return new_user


@app.get("/api/v1/users/me")
def read_users_me(user=Depends(retrieve_user_by_access_token)):
    return {"username": user.username}


_news_id_counter = itertools.count(start=1000000)


def get_upvote_status(news_id, user_id, database):
    upvote_users_count = (
        database.query(user_news_association_table)
        .filter_by(news_articles_id=news_id)
        .count()
    )
    does_user_upvote = False
    if user_id:
        does_user_upvote = (
                database.query(user_news_association_table)
                .filter_by(news_articles_id=news_id, user_id=user_id)
                .first()
                is not None
        )
    return upvote_users_count, does_user_upvote


@app.get("/api/v1/news/news")
def read_news(database=Depends(session_opener)):
    """
    read news

    :param database:
    :return:
    """
    news_list = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    news_list_adding_upvote_status = []
    for news in news_list:
        upvotes, is_upvoted = get_upvote_status(news.id, None, database)
        news_list_adding_upvote_status.append(
            {**news.__dict__, "upvotes": upvotes, "is_upvoted": is_upvoted}
        )
    return news_list_adding_upvote_status


@app.get(
    "/api/v1/news/user_news"
)
def read_user_news(
        database=Depends(session_opener),
        user=Depends(retrieve_user_by_access_token)
):
    """
    read user news

    :param database:
    :param user:
    :return:
    """
    news_list = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    news_list_adding_upvote_status = []
    for news in news_list:
        upvotes, is_upvoted = get_upvote_status(news.id, user.id, database)
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
    news_snapshots = fetch_news_snapshots(keywords, is_initial=False)
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
            news["id"] = next(_news_id_counter)
            news_list.append(news)
        except Exception as e:
            print(e)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)

class NewsSummaryRequestSchema(BaseModel):
    content: str

@app.post("/api/v1/news/news_summary")
async def summarize_news(
        news: NewsSummaryRequestSchema, user=Depends(retrieve_user_by_access_token)
):
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
        database=Depends(session_opener),
        user=Depends(retrieve_user_by_access_token),
):
    message = toggle_upvote(id, user.id, database)
    return {"message": message}


def toggle_upvote(news_id, user_id, database):
    existing_upvote = database.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        deletion_statement = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
        database.execute(deletion_statement)
        database.commit()
        return "Upvote removed"
    else:
        insertion_statement = insert(user_news_association_table).values(
            news_articles_id=news_id, user_id=user_id
        )
        database.execute(insertion_statement)
        database.commit()
        return "Article upvoted"


def does_news_exist(id, database: Session):
    return database.query(NewsArticle).filter_by(id=id).first() is not None


@app.get("/api/v1/prices/necessities-price")
def read_necessities_prices(
        category=Query(None), commodity=Query(None)
):
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json()
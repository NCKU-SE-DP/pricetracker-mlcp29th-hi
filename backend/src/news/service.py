import itertools
import json
from urllib.parse import quote

from openai import OpenAI
import requests
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from .config import configuration
from ..models import NewsArticle, User, user_news_association_table
from ..crawler.crawler_base import NewsWithSummary
from ..crawler.udn_crawler import UDNCrawler


_news_id_counter = itertools.count(start=1000000)
crawler = UDNCrawler()


def _generate_news_id() -> int:
    return next(_news_id_counter)


def _does_news_exist(news_id: int, database: Session) -> bool:
    return database.query(NewsArticle).filter_by(id=news_id).first() is not None


def _get_upvote_status(news_id: int, user_id: int, database: Session) -> tuple[int, int]:
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


def _ask_OpenAI(system_prompt: str, user_prompt: str) -> str | None:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    completion = OpenAI(api_key=configuration.open_ai_api_key).chat.completions.create(
        model=configuration.open_ai_model,
        messages=messages
    )
    response = completion.choices[0].message.content
    return response


def _extract_search_keywords(news_expectation: str) -> str | None:
    keywords = _ask_OpenAI(
        system_prompt="你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        user_prompt=news_expectation
    )
    return keywords


def _search(search_term: str, is_initial=False):
    if is_initial:
        return crawler.search_initially(search_term)
    return crawler.search(search_term, page=1)


def retrieve_news_with_upvote_status(database: Session, user: User | None) -> list:
    news_list = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    news_list_adding_upvote_status = []
    for news in news_list:
        upvotes, is_upvoted = _get_upvote_status(news.id, (None if user is None else user.id), database)
        news_list_adding_upvote_status.append(
            {**news.__dict__, "upvotes": upvotes, "is_upvoted": is_upvoted}
        )
    return news_list_adding_upvote_status


def search_news(prompt: str) -> list:
    news_list = []
    keywords = _extract_search_keywords(prompt)
    # TODO: should change into simple factory pattern
    news_snapshots = _search(keywords, is_initial=False)
    for snapshot in news_snapshots:
        try:
            news = crawler.validate_and_parse(snapshot.url).model_dump()
            news["id"] = _generate_news_id()
            news_list.append(news)
        except Exception as exception:
            print(exception)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)


def summarize_news(content: str) -> dict:
    summary = _ask_OpenAI(
        system_prompt="你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        user_prompt=content
    )
    return json.loads(summary)


def toggle_upvote(news_id: int, user_id: int, database: Session) -> str:
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


def download_price_changes_news(database: Session, is_initial=False):
    news_snapshots = _search("價格", is_initial=is_initial)
    for snapshot in news_snapshots:
        relevance = _ask_OpenAI(
            system_prompt="你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            user_prompt=snapshot["title"]
        )
        if relevance == "high":
            news = crawler.validate_and_parse(snapshot.url)
            summary = summarize_news(news.content)
            news_with_summary = NewsWithSummary(
                title=news.title,
                url=news.url,
                time=news.time,
                content=news.content,
                summary=summary["影響"],
                reason=summary["原因"]
            )
            crawler.save(news_with_summary, database)
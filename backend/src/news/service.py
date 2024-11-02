from bs4 import BeautifulSoup
import itertools
import json
from openai import OpenAI
import requests
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from urllib.parse import quote
from .config import configuration
from ..database import get_database
from ..models import NewsArticle, user_news_association_table


_news_id_counter = itertools.count(start=1000000)

def generate_news_id() -> int:
    return next(_news_id_counter)

def save_news(news):
    """
    save news to database
    :param news:
    :return:
    """
    session = get_database()
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
            response = requests.get(configuration.news_snapshot_api_url, params=parameters)
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
        response = requests.get(configuration.news_snapshot_api_url, params=parameters)

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
        completion = OpenAI(api_key=configuration.open_ai_api_key).chat.completions.create(
            model=configuration.open_ai_model,
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

            completion = OpenAI(api_key=configuration.open_ai_api_key).chat.completions.create(
                model=configuration.open_ai_model,
                messages=messages,
            )
            summary = completion.choices[0].message.content
            summary = json.loads(summary)
            news["summary"] = summary["影響"]
            news["reason"] = summary["原因"]
            save_news(news)

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

def does_news_exist(news_id, database: Session):
    return database.query(NewsArticle).filter_by(id=news_id).first() is not None

# def generate_summary(content):
#     m = [
#         {
#             "role": "system",
#             "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
#         },
#         {"role": "user", "content": f"{content}"},
#     ]
#
#     completion = OpenAI(api_key=configuration.open_ai_api_key).chat.completions.create(
#         model=configuration.open_ai_model,
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
#     completion = OpenAI(api_key=configuration.open_ai_api_key).chat.completions.create(
#         model=configuration.open_ai_model,
#         messages=m,
#     )
#     return completion.choices[0].message.content
from bs4 import BeautifulSoup
from fastapi import APIRouter
import json
from openai import OpenAI
import requests
from src.dependencies import DatabaseSession
from src.models import NewsArticle
from src.user.dependencies import CurrentLoggedInUser
from . import service
from .schemas import NewsSummaryRequestSchema, SearchRequestSchema

router = APIRouter(prefix="/api/v1/news")

@router.get("/news")
def read_news(database: DatabaseSession):
    """
    read news

    :param database:
    :return:
    """
    news_list = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    news_list_adding_upvote_status = []
    for news in news_list:
        upvotes, is_upvoted = service.get_upvote_status(news.id, None, database)
        news_list_adding_upvote_status.append(
            {**news.__dict__, "upvotes": upvotes, "is_upvoted": is_upvoted}
        )
    return news_list_adding_upvote_status


@router.get("/user_news")
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
        upvotes, is_upvoted = service.get_upvote_status(news.id, user.id, database)
        news_list_adding_upvote_status.append(
            {
                **news.__dict__,
                "upvotes": upvotes,
                "is_upvoted": is_upvoted,
            }
        )
    return news_list_adding_upvote_status


@router.post("/search_news")
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
    news_snapshots = service.fetch_news_snapshots(keywords, is_initial=False)
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
            news["id"] = service.generate_news_id()
            news_list.append(news)
        except Exception as exception:
            print(exception)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)


@router.post("/news_summary")
async def summarize_news(news: NewsSummaryRequestSchema, user: CurrentLoggedInUser):
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


@router.post("/{news_id}/upvote")
def upvote_news(
        news_id: int,
        database: DatabaseSession,
        user: CurrentLoggedInUser
):
    message = service.toggle_upvote(news_id, user.id, database)
    return {"message": message}
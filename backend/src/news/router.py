from fastapi import APIRouter

from src.dependencies import DatabaseSession
from src.user.dependencies import CurrentLoggedInUser
from . import service
from .schemas import NewsSummaryRequestSchema, NewsSummaryCustomModelRequestSchema, SearchRequestSchema

router = APIRouter(prefix="/api/v1/news")

@router.get("/news")
def read_news(database: DatabaseSession):
    return service.retrieve_news_with_upvote_status(database, None)


@router.get("/user_news")
def read_user_news(database: DatabaseSession, user: CurrentLoggedInUser):
    return service.retrieve_news_with_upvote_status(database, user)


@router.post("/search_news")
async def search_news(search_query: SearchRequestSchema):
    return service.search_news(search_query.prompt)


@router.post("/news_summary")
async def summarize_news(news: NewsSummaryRequestSchema, user: CurrentLoggedInUser):
    return service.summarize_news(news.content)


@router.post("/news_summary_custom_model")
async def summarize_news_with_custome_model(schema: NewsSummaryCustomModelRequestSchema, user: CurrentLoggedInUser):
    return service.summarize_news(schema.content, schema.ai_model)


@router.post("/{news_id}/upvote")
def upvote_news(
        news_id: int,
        database: DatabaseSession,
        user: CurrentLoggedInUser
):
    message = service.toggle_upvote(news_id, user.id, database)
    return {"message": message}
import itertools

from sentry_sdk import capture_exception
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from .constants import AIModel
from .exceptions import NewsNotFoundError
from ..models import NewsArticle, User, user_news_association_table
from ..crawler.base import NewsSnapshot, NewsWithSummary
from ..crawler.exceptions import NewsExtractionError
from ..crawler.udn_crawler import UDNCrawler
from ..llm_client.clients import AnthropicClient, OpenAIClient
from ..llm_client.constants import RelevanceLevel
from ..llm_client.schemas import NewsSummary
from ..llm_client.template import LLMClientTemplate
from ..logger import Logger


_news_id_counter = itertools.count(start=1000000)
_crawler = UDNCrawler()
_llm_client = OpenAIClient()


def _generate_news_id() -> int:
    return next(_news_id_counter)


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


def _search(search_term: str, is_initial=False) -> list[NewsSnapshot]:
    if is_initial:
        return _crawler.search_initially(search_term)
    return _crawler.search(search_term, page=1)


def retrieve_news_with_upvote_status(database: Session, user: User | None) -> list[dict]:
    news_list = database.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    news_list_adding_upvote_status = []
    for news in news_list:
        upvotes, is_upvoted = _get_upvote_status(news.id, (None if user is None else user.id), database)
        news_list_adding_upvote_status.append(
            {**news.__dict__, "upvotes": upvotes, "is_upvoted": is_upvoted}
        )
    return news_list_adding_upvote_status


def search_news(prompt: str) -> list[dict]:
    news_list = []
    keywords = _llm_client.extract_search_keywords(prompt)
    # TODO: should change into simple factory pattern
    news_snapshots = _search(keywords, is_initial=False)
    for snapshot in news_snapshots:
        try:
            news = _crawler.validate_and_parse(snapshot.url).model_dump()
            news["id"] = _generate_news_id()
            news_list.append(news)
        except NewsExtractionError as exception: 
            capture_exception(exception)
            Logger().log_error(exception)
    return sorted(news_list, key=lambda x: x["time"], reverse=True)


def toggle_upvote(news_id: int, user_id: int, database: Session) -> str:
    does_news_exist = database.query(NewsArticle).filter(NewsArticle.id == news_id).first() is not None
    if not does_news_exist:
        raise NewsNotFoundError
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
        relevance = _llm_client.evaluate_relevance_to_price_changes(snapshot.title)
        if relevance == RelevanceLevel.HIGH:
            news = _crawler.validate_and_parse(snapshot.url)
            summary = _llm_client.summarize_news(news.content)
            news_with_summary = NewsWithSummary(
                **news.model_dump(),
                **summary.model_dump()
            )
            _crawler.save(news_with_summary, database)


def summarize_news(news_content: str, ai_model: AIModel = AIModel.OPENAI) -> NewsSummary:
    llm_client_types = {
        AIModel.OPENAI   : OpenAIClient,
        AIModel.ANTHROPIC: AnthropicClient
    }
    client: LLMClientTemplate = llm_client_types[ai_model]()
    return client.summarize_news(news_content)
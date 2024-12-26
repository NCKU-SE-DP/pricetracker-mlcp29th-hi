"""
UDN News Scraper Module

This module provides the UDNCrawler class for fetching, parsing, and saving news from the UDN website.
The class extends the NewsCrawlerBase and includes functionalities to search for news based on a search term,
parse the details of individual news, and save them to a database using SQLAlchemy ORM.

Classes:
    UDNCrawler: A class to scrape news from UDN.

Exceptions:
    DomainMismatchException: Raised when the URL domain does not match the expected domain for the crawler.

Usage Example:
    crawler = UDNCrawler(timeout=10)
    snapshots = crawler.startup("technology")
    for snapshot in snapshots:
        news = crawler.parse(snapshot.url)
        crawler.save(news, db_session)

UDNCrawler Methods:
    __init__(self, timeout: int = 5): Initializes the crawler with a default timeout for HTTP requests.
    search_initially(self, search_term: str) -> list[NewsSnapshot]: Fetches news snapshots for a given search term across multiple pages.
    search(self, search_term: str, page: int | tuple[int, int]) -> list[NewsSnapshot]: Fetches news snapshots for specified pages.
    save(self, news: NewsWithSummary, db: Session): Saves a news with summary added to the database.
    _perform_search(self, page: int, search_term: str) -> list[NewsSnapshot]: Internal helper method to fetch news snapshots for a specific page.
    _create_search_params(self, page: int, search_term: str): Creates the parameters for the search request.
    _parse_snapshots(response): Internal helper method to parse news snapshots from the given response of a search request.
    _parse(self, url: str) -> News: Internal helper method to parses the news from a given validated URL. Instead of calling this method directly, this method should only be called by `validate_and_parse`, which is inherited from `NewsCrawlerBase`.
    _extract_news(soup, url: str) -> News: Internal help method to extract news details from the BeautifulSoup object.
    _perform_request(self, params: dict): Performs the HTTP request to fetch news data.
"""

from bs4 import BeautifulSoup
from pydantic import TypeAdapter
import requests
from requests import Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from urllib.parse import quote

from .base import NewsCrawlerBase, NewsSnapshot, News, NewsWithSummary
from .exceptions import NewsExtractionError
from ..models import NewsArticle


class UDNCrawler(NewsCrawlerBase):
    NEWS_WEBSITE_URL = "https://udn.com/api/more"
    CHANNEL_ID = 2

    def __init__(self, timeout: int = 5) -> None:
        self.timeout = timeout

    def search_initially(self, search_term: str) -> list[NewsSnapshot]:
        """
        Initializes the application by fetching news snapshots for a given search term across multiple pages.
        This method is typically called at the beginning of the program when there is no data available,
        hence it fetches snapshots from the first 10 pages.

        :param search_term: The term to search for in news snapshots.
        :return: A list of NewsSnapshot namedtuples containing the title and URL of news articles.
        :rtype: list[NewsSnapshot]
        """
        return self.search(search_term, page=(1, 10))

    def search(
        self, search_term: str, page: int | tuple[int, int]
    ) -> list[NewsSnapshot]:
        page_range = range(page, page + 1) if isinstance(page, int) else range(page[0], page[1] + 1)
        snapshots = []
        for page in page_range:
            snapshots.extend(self._perform_search(page, search_term))
        return snapshots

    def save(self, news: NewsWithSummary, db: Session):
        existing_news = db.query(NewsArticle).filter_by(content = news.content).first()
        if existing_news is None:
            try:
                db.add(NewsArticle(**news.model_dump()))
            except SQLAlchemyError:
                db.rollback()
                raise
            else:
                db.commit()

    def _perform_search(self, page: int, search_term: str) -> list[NewsSnapshot]:
        parameters = self._create_search_params(page, search_term)
        response = self._perform_request(self.NEWS_WEBSITE_URL, parameters)
        snapshots = UDNCrawler._parse_snapshots(response)
        return snapshots
    
    def _create_search_params(self, page: int, search_term: str) -> dict:
        parameters = {
            "page": page,
            "id": f"search:{quote(search_term)}",
            "channelId": self.CHANNEL_ID,
            "type": "searchword",
        }
        return parameters

    @staticmethod
    def _parse_snapshots(response: Response) -> list[NewsSnapshot]:
        return TypeAdapter(list[NewsSnapshot]).validate_python(response.json()["lists"])
    
    def _parse(self, url: str) -> News:
        response = self._perform_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        news = self._extract_news(soup, url)
        return news
    
    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
        try:
            title = soup.find("h1", class_="article-content__title").text
            time = soup.find("time", class_="article-content__time").text
            content_section = soup.find("section", class_="article-content__editor")
            paragraphs = [
                paragraph.text
                for paragraph in content_section.find_all("p")
                if paragraph.text.strip() != "" and "▪" not in paragraph.text
            ]
            content = " ".join(paragraphs)
            return News(title=title, url=url, time=time, content=content)
        except AttributeError as exception:
            raise NewsExtractionError(url)

    def _perform_request(self, url: str | None = None, params: dict | None = None) -> Response:
        return requests.get(url=url, params=params, timeout=self.timeout)
"""
UDN News Scraper Module

This module provides the UDNCrawler class for fetching, parsing, and saving news articles from the UDN website.
The class extends the NewsCrawlerBase and includes functionalities to search for news articles based on a search term,
parse the details of individual articles, and save them to a database using SQLAlchemy ORM.

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
    _perform_search(self, page: int, search_term: str) -> list[NewsSnapshot]: Helper method to fetch news snapshots for a specific page.
    _create_search_params(self, page: int, search_term: str): Creates the parameters for the search request.
    _perform_request(self, params: dict): Performs the HTTP request to fetch news data.
    _parse_snapshots(response): Parses the response to extract news snapshots.
    parse(self, url: str) -> News: Parses a news article from a given URL.
    _extract_news(soup, url: str) -> News: Extracts news details from the BeautifulSoup object.
    save(self, news: News, db: Session): Saves a news article to the database.
"""

import requests
from requests import Response
from bs4 import BeautifulSoup
from pydantic import TypeAdapter
from sqlalchemy.orm import Session
from urllib.parse import quote

from .crawler_base import NewsCrawlerBase, NewsSnapshot, News, NewsWithSummary


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

        # Calculate the range of pages to fetch news from.
        # If 'page' is a tuple, unpack it and create a range representing those pages (inclusive).
        # If 'page' is an int, create a list containing only that single page number.
        # page_range = range(*page) if isinstance(page, tuple) else [page]
        ...

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

    def _perform_request(self, url: str | None = None, params: dict | None = None) -> Response:
        return requests.get(url=url, params=params, timeout=self.timeout)

    @staticmethod
    def _parse_snapshots(response: Response) -> list[NewsSnapshot]:
        return TypeAdapter(list[NewsSnapshot]).validate_python(response.json()["lists"])

    def parse(self, url: str) -> News:
        ...

    @staticmethod
    def _extract_news(soup: BeautifulSoup, url: str) -> News:
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

    def save(self, news: NewsWithSummary, db: Session):
        ...
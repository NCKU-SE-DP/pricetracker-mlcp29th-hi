from bs4 import BeautifulSoup


def parse_news_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1", class_="article-content__title").text
    time = soup.find("time", class_="article-content__time").text
    content_section = soup.find("section", class_="article-content__editor")

    paragraphs = [
        paragraph.text
        for paragraph in content_section.find_all("p")
        if paragraph.text.strip() != "" and "▪" not in paragraph.text
    ]

    return {"title": title, "time": time, "content": " ".join(paragraphs)}
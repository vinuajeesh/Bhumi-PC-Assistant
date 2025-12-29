from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class WebSearch:
    def __init__(self):
        self.ddgs = DDGS()

    def search_web(self, query, max_results=3):
        """Searches the web using DuckDuckGo."""
        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            if not results:
                return "I couldn't find anything on that. The internet must be broken. 🤷‍♀️"

            summary = "Here's what I found:\n"
            for i, res in enumerate(results):
                summary += f"{i+1}. {res['title']}: {res['body']}\nLink: {res['href']}\n\n"
            return summary
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"I tripped over a network cable while searching. Error: {e}"

    def fetch_tech_news(self):
        """Fetches top tech stories (e.g. from Hacker News or similar)."""
        # Using Hacker News API for reliability over scraping raw HTML if possible,
        # or just scraping a site.
        # User asked for "NewsScraper that fetches top 5 tech stories".
        # Hacker News API is cleanest.

        try:
            # Get top stories IDs
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(top_stories_url)
            story_ids = response.json()[:5]

            news_summary = "🔥 Top Tech News:\n"

            for sid in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                story_data = requests.get(story_url).json()
                title = story_data.get('title', 'No Title')
                url = story_data.get('url', 'No URL')
                news_summary += f"- {title} ({url})\n"

            return news_summary

        except Exception as e:
            logger.error(f"News fetch error: {e}")
            return "I couldn't fetch the news. Maybe big tech is censoring me? 😜"

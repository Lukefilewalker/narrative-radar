import feedparser

from app.db import save_item
from app.config.feeds import RSS_FEEDS
from app.config.reddit_feeds import REDDIT_FEEDS


def collect_rss():
    count = 0

    all_feeds = {}
    all_feeds.update(RSS_FEEDS)
    all_feeds.update(REDDIT_FEEDS)

    for source, url in all_feeds.items():

        feed = feedparser.parse(
            url,
            agent="RabbitHoleRadar/1.0"
        )

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "").strip()
            published = entry.get("published", "")

            if not title or not link:
                continue

            inserted = save_item(
                source,
                title,
                link,
                summary,
                published
            )

            if inserted:
                count += 1

    return count

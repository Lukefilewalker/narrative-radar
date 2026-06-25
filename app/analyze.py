"""
Analyze collected items and build Discord-ready reports.

This file does the "thinking" layer for Rabbit Hole Radar:

1. Pulls recent items from SQLite.
2. Cleans titles and summaries.
3. Categorizes items into conspiracy/rabbit-hole topic buckets.
4. Extracts named entities with spaCy.
5. Saves category snapshots for trend tracking.
6. Builds the plain-text Discord report.
7. Builds Discord embeds with clickable story links.

Most keywords and tuning lists live in app/config/.
Keep this file mostly focused on logic.

Author:
Steven P. Walker
stevenpaintewalker@gmail.com
"""

import re
import html
import spacy

from collections import Counter
from datetime import datetime, timedelta, timezone

from app.db import (
    get_items_since,
    save_category_snapshot,
    get_category_snapshot,
)
from app.config.blacklist import ENTITY_BLACKLIST
from app.config.aliases import ENTITY_ALIASES
from app.config.stopwords import STOPWORDS
from app.config.categories import TOPIC_CATEGORIES


# Load spaCy's small English model once when the module starts.
# Used for named entity extraction, like "Epstein", "Trump", "QAnon", etc.
nlp = spacy.load("en_core_web_sm")


def normalize_entity(name):
    """
    Convert alternate entity names into one preferred name.

    Example:
    "Jeffrey Epstein" -> "Epstein"
    "Donald Trump" -> "Trump"

    The mappings live in app/config/aliases.py.
    """
    name = name.strip()
    return ENTITY_ALIASES.get(name, name)


def clean_text(text):
    """
    Clean RSS/Reddit/Google News text before analysis.

    This removes:
    - HTML entities
    - HTML tags
    - URLs
    - weird punctuation
    - extra whitespace
    """
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text):
    """
    Break text into searchable words.

    Short words and common filler words are ignored.
    The STOPWORDS list lives in app/config/stopwords.py.
    """
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9'-]{3,}\b", text.lower())
    return [w for w in words if w not in STOPWORDS]


def extract_entities(items):
    """
    Use spaCy to extract named entities from recent item titles.

    This helps the report answer:
    "Who or what keeps showing up?"

    Examples:
    - Epstein
    - QAnon
    - Trump
    - Bigfoot
    - Mothman

    News outlets and noisy entities are filtered with ENTITY_BLACKLIST.
    """
    entity_counts = Counter()

    for item in items:
        title = clean_text(item.get("title", ""))
        doc = nlp(title)

        for ent in doc.ents:
            if ent.label_ not in {
                "PERSON", "ORG", "GPE", "EVENT", "PRODUCT", "NORP"
            }:
                continue

            entity = normalize_entity(ent.text)

            if entity in ENTITY_BLACKLIST:
                continue

            if len(entity) < 3:
                continue

            entity_counts[entity] += 1

    return entity_counts.most_common(15)


def categorize_items(items):
    """
    Count how many recent items match each configured topic category.

    Categories live in app/config/categories.py.

    An item can count toward more than one category if it contains
    keywords from multiple buckets. That is intentional for now because
    stories often overlap, like "UFO + Epstein" or "QAnon + Deep State".
    """
    category_counts = Counter()

    for item in items:
        text = clean_text(
            f"{item.get('title', '')} {item.get('summary', '')}"
        ).lower()

        for category, keywords in TOPIC_CATEGORIES.items():
            for keyword in keywords:
                if keyword in text:
                    category_counts[category] += 1
                    break

    return category_counts.most_common()


def get_category_highlights(items, limit_per_category=2):
    """
    Pick a few example stories for each category.

    These examples become the clickable Discord embed links.

    Unlike category counting, each story is assigned to the first matching
    category only. This keeps the embed section from repeating the same
    headline under several categories.
    """
    highlights = {category: [] for category in TOPIC_CATEGORIES}
    seen_titles = {category: set() for category in TOPIC_CATEGORIES}

    for item in items:
        title = clean_text(item.get("title", ""))
        summary = clean_text(item.get("summary", ""))
        url = item.get("url", "")

        if not title or not url:
            continue

        text = f"{title} {summary}".lower()

        for category, keywords in TOPIC_CATEGORIES.items():
            if any(keyword in text for keyword in keywords):
                if title not in seen_titles[category]:
                    highlights[category].append({
                        "title": title,
                        "url": url,
                    })
                    seen_titles[category].add(title)

                break

    return {
        category: stories[:limit_per_category]
        for category, stories in highlights.items()
        if stories
    }


def calculate_trends(top_categories):
    """
    Save today's category counts and compare them against yesterday.

    First day behavior:
    If there is no snapshot from yesterday, every category will show
    as a positive change. That is expected on initial setup.

    The snapshot table is managed in app/db.py.
    """
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)

    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()

    save_category_snapshot(today_str, top_categories)
    yesterday_counts = get_category_snapshot(yesterday_str)

    trends = []

    for category, count in top_categories:
        previous = yesterday_counts.get(category, 0)
        change = count - previous

        if change == 0:
            continue

        trends.append({
            "category": category,
            "current": count,
            "previous": previous,
            "change": change,
        })

    trends.sort(key=lambda item: abs(item["change"]), reverse=True)

    return trends


def analyze_recent():
    """
    Main analysis entry point.

    Pulls items from the last 48 hours, then calculates:
    - top categories
    - category highlights
    - top entities
    - category trends
    - simple topic phrases

    The 48-hour window is a good default for slower-moving conspiracy,
    cryptid, and fringe-topic chatter.
    """
    items = get_items_since(hours=48)

    # Simple phrase-ish topic extraction.
    # This is less important now that category highlights exist, but it is
    # kept in the result for future experiments.
    topic_counter = Counter()
    topic_examples = {}

    for item in items:
        title = clean_text(item.get("title", ""))

        words = [
            w for w in tokenize(title)
            if len(w) > 4
        ]

        if not words:
            continue

        topic = " ".join(words[:3])
        topic_counter[topic] += 1

        if topic not in topic_examples:
            topic_examples[topic] = title

    top_topics = []

    for topic, count in topic_counter.most_common(10):
        top_topics.append({
            "topic": topic,
            "count": count,
            "example": topic_examples[topic],
        })

    top_entities = extract_entities(items)
    top_categories = categorize_items(items)
    trends = calculate_trends(top_categories)
    category_highlights = get_category_highlights(items)

    return {
        "item_count": len(items),
        "top_categories": top_categories,
        "category_highlights": category_highlights,
        "top_topics": top_topics,
        "top_entities": top_entities,
        "trends": trends,
        "recent_items": items[:10],
    }


def format_report(result):
    """
    Build the plain-text part of the Discord message.

    The clickable story links are handled separately in build_embeds().
    Keeping the plain text shorter makes the Discord post easier to scan.
    """
    lines = []

    lines.append("🛸 Rabbit Hole Radar")
    lines.append("")
    lines.append(f"Items scanned: {result['item_count']} from the last 48 hours")

    lines.append("")
    lines.append("Top Categories")
    lines.append("")

    for category, count in result["top_categories"][:7]:
        lines.append(f"• {category} ({count})")

    if result["trends"]:
        lines.append("")
        lines.append("Biggest Changes vs Yesterday")
        lines.append("")

        for trend in result["trends"][:5]:
            sign = "+" if trend["change"] > 0 else ""
            lines.append(
                f"• {trend['category']} {sign}{trend['change']} "
                f"since yesterday"
            )

    lines.append("")
    lines.append("Most Mentioned Entities")
    lines.append("")

    for entity, count in result["top_entities"][:10]:
        lines.append(f"• {entity} ({count})")

    lines.append("")
    lines.append(
        "Pattern report only. Not a verification of claims."
    )

    return "\n".join(lines)


def build_embeds(result):
    """
    Build Discord embed cards for the top categories.

    Each embed represents one category and contains up to two clickable
    story links.

    Discord limits:
    - Max 10 embeds per message
    - Field value max is 1024 characters
    - Embed description max is 4096 characters

    We currently send only the top 5 categories to keep the post readable.
    """
    embeds = []

    for category, count in result["top_categories"][:5]:
        highlights = result["category_highlights"].get(category, [])[:2]

        if not highlights:
            continue

        fields = []

        for idx, story in enumerate(highlights, start=1):
            title = story.get("title", "Untitled")
            url = story.get("url", "")

            if url:
                value = f"[{title}]({url})"
            else:
                value = title

            fields.append({
                "name": f"Story {idx}",
                "value": value[:1024],
                "inline": False,
            })

        embeds.append({
            "title": f"{category} ({count})",
            "fields": fields,
        })

    return embeds

# 🛸 Rabbit Hole Radar

Rabbit Hole Radar is a Raspberry Pi-friendly Python application that monitors conspiracy theories, fringe narratives, UFO/UAP discussions, cryptids, high-strangeness topics, and emerging online rabbit holes.

The system collects stories from RSS feeds and Reddit communities, analyzes them using Natural Language Processing (spaCy), categorizes them into topic areas, tracks trends over time, and publishes automated intelligence-style reports to Discord.

## Features

- RSS feed collection
- Reddit RSS monitoring
- SQLite storage
- NLP entity extraction with spaCy
- Topic categorization
- Trend tracking
- Discord webhook reporting
- Clickable Discord story embeds
- Historical category snapshots
- Raspberry Pi compatible

## Current Categories

- 👽 UFO / UAP
- 🦍 Cryptozoology
- 👁 QAnon
- 🧪 Chemtrails
- 📁 Epstein
- 🌎 Flat Earth
- 🏛 Deep State
- 🔺 Illuminati

Additional categories can be added through configuration files.

## Example Report

Each report includes:

- Top Categories
- Biggest Changes vs Yesterday
- Most Mentioned Entities
- Category Highlight Stories
- Clickable Discord Links

## Project Structure

```text
app/
├── analyze.py
├── db.py
├── collectors/
├── reports/
└── config/

data/
└── narratives.db
```

## Configuration
Most customization lives in:

- app/config/categories.py
- app/config/feeds.py
- app/config/reddit_feeds.py
- app/config/aliases.py
- app/config/blacklist.py
- app/config/stopwords.py

## Installation
create a virtual environment
```
python -m venv .venv
```

Activate it:
```
source .venv/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```

Create a .env file:
```
DISCORD_WEBHOOK_URL=your_webhook_here
```

Run the application:
```
python -m app.run
```

## Roadmap
- Additional Reddit communities
- YouTube transcript ingestion
- Podcast monitoring
- Historical trend charts
- Source weighting
- Discord slash commands
- Grafana dashboard
- Weekly narrative reports

## Disclaimer
Rabbit Hole Radar tracks discussion patterns and narrative trends.

It does not verify claims, determine truthfulness, or endorse any topic being discussed.

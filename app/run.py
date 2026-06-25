from app.db import init_db
from app.collectors.rss import collect_rss
from app.analyze import analyze_recent, format_report, build_embeds
from app.reports.discord import post_to_discord


def main():
    init_db()

    collected = collect_rss()
    result = analyze_recent()
    report = format_report(result)

    print(f"Collected RSS entries: {collected}")
    print()
    print(report)

    embeds = build_embeds(result)
    post_to_discord(report, embeds=embeds)


if __name__ == "__main__":
    main()

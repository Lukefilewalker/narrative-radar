from app.reports.discord import post_to_discord

message = """🛸 Rabbit Hole Radar test post

The bot is alive.

Current status:
- RSS collection works
- SQLite storage works
- Basic topic report works
- Smarter analysis coming next

Pattern report only. Not a verification of claims.
"""

post_to_discord(message)

print("Test post sent.")

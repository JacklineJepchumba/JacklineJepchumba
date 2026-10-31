"""Rewrites the activity block in README.md with the latest public commits.

Reads the owner's public events from the GitHub API (no extra secrets needed),
keeps the five most recent commits, and writes them between the
<!--ACTIVITY:START--> and <!--ACTIVITY:END--> markers.
"""
import json
import os
import re
import urllib.request

OWNER = os.environ["GITHUB_REPOSITORY_OWNER"]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
LIMIT = 5

req = urllib.request.Request(
    f"https://api.github.com/users/{OWNER}/events/public?per_page=50",
    headers={
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    },
)
with urllib.request.urlopen(req, timeout=30) as r:
    events = json.load(r)

rows = []
for ev in events:
    if ev.get("type") != "PushEvent":
        continue
    repo = ev["repo"]["name"].split("/")[-1]
    if repo == OWNER:  # skip the profile repo itself (the bot's own commits)
        continue
    day = ev["created_at"][:10]
    for c in reversed(ev["payload"].get("commits", [])):
        msg = c["message"].splitlines()[0].replace("`", "'")
        msg = msg if len(msg) <= 58 else msg[:55] + "..."
        rows.append(f"{day}  {repo[:22]:<22}  {msg}")
    if len(rows) >= LIMIT:
        break

rows = rows[:LIMIT] or ["no public commits found yet"]
block = "```text\n$ git log --all --oneline -n 5\n" + "\n".join(rows) + "\n```"

with open("README.md", encoding="utf-8") as f:
    text = f.read()
new = re.sub(
    r"<!--ACTIVITY:START-->.*?<!--ACTIVITY:END-->",
    lambda _: f"<!--ACTIVITY:START-->\n{block}\n<!--ACTIVITY:END-->",
    text,
    flags=re.S,
)
if new != text:
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new)

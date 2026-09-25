#!/usr/bin/env python3
import html
import json
import os
import urllib.request
from pathlib import Path

USER = os.environ.get("GITHUB_USERNAME", "nabeelsyed11")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = Path("generated-widgets")
OUT.mkdir(exist_ok=True)

def get(path):
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "User-Agent": "github-profile-widgets",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def e(value):
    return html.escape(str(value), quote=True)

def svg(title, content, height=360):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}">
<rect width="100%" height="100%" rx="12" fill="#0d1117"/>
<text x="32" y="52" fill="#87ceeb" font-family="Arial,sans-serif" font-size="26" font-weight="700">{e(title)}</text>
{content}
</svg>'''

def text(x, y, value, size=16, color="#c9d1d9", weight="400"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{weight}">{e(value)}</text>'

profile = get(f"/users/{USER}")
repos = get(f"/users/{USER}/repos?per_page=100&sort=pushed")
events = get(f"/users/{USER}/events/public?per_page=100")

days = {}
for event in events:
    day = event.get("created_at", "")[:10]
    if day:
        days[day] = days.get(day, 0) + 1

bars = []
for index, (day, count) in enumerate(sorted(days.items())[-30:]):
    bar_height = 20 + min(count, 8) * 22
    x = 35 + index * 30
    bars.append(f'<rect x="{x}" y="300" width="18" height="-{bar_height}" rx="3" fill="#2f81f7"><title>{e(day)}: {count} public events</title></rect>')

activity = text(35, 335, "Last 30 days of public activity • refreshed by GitHub Actions", 14, "#8b949e") + "".join(bars)
(OUT / "activity.svg").write_text(svg("GitHub Activity Graph", activity), encoding="utf-8")

stats = [("Repositories", profile.get("public_repos", 0)), ("Followers", profile.get("followers", 0)), ("Following", profile.get("following", 0)), ("Gists", profile.get("public_gists", 0))]
trophies = ""
for index, (label, value) in enumerate(stats):
    x = 35 + index * 235
    trophies += f'<rect x="{x}" y="90" width="205" height="155" rx="10" fill="#161b22" stroke="#30363d"/>'
    trophies += text(x + 20, 130, "TROPHY", 13, "#f2cc60", "700")
    trophies += text(x + 20, 175, value, 28, "#f0f6fc", "700")
    trophies += text(x + 20, 210, label, 15, "#8b949e")
(OUT / "trophies.svg").write_text(svg("GitHub Profile Trophies", trophies, 285), encoding="utf-8")

top = sorted(repos, key=lambda repo: (repo.get("stargazers_count", 0), repo.get("forks_count", 0), repo.get("pushed_at", "")), reverse=True)[:5]
rows = ""
for index, repo in enumerate(top):
    y = 95 + index * 42
    rows += text(35, y, f"{index + 1}. {repo.get('name', 'repository')}", 17, "#58a6ff", "700")
    rows += text(450, y, f"stars: {repo.get('stargazers_count', 0)} • forks: {repo.get('forks_count', 0)}", 15, "#8b949e")
(OUT / "top-repositories.svg").write_text(svg("Top Repositories", rows, max(150, 125 + len(top) * 42)), encoding="utf-8")

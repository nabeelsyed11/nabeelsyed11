#!/usr/bin/env python3
import html
import json
import os
import urllib.parse
import urllib.request
from collections import Counter
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


def esc(value):
    return html.escape(str(value), quote=True)


def label(x, y, value, size=16, color="#c9d1d9", weight="400"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{weight}">{esc(value)}</text>'


def document(title, body, height=360):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}">
<rect width="100%" height="100%" rx="12" fill="#0d1117"/>
<text x="32" y="52" fill="#87ceeb" font-family="Arial,sans-serif" font-size="26" font-weight="700">{esc(title)}</text>
{body}
</svg>'''


profile = get(f"/users/{urllib.parse.quote(USER)}")
repos = get(f"/users/{urllib.parse.quote(USER)}/repos?per_page=100&sort=pushed")
events = get(f"/users/{urllib.parse.quote(USER)}/events/public?per_page=100")

# Statistics and language data are generated locally from the GitHub REST API.
total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
total_forks = sum(repo.get("forks_count", 0) for repo in repos)
contributions = sum(1 for event in events if event.get("type") in {"PushEvent", "PullRequestEvent", "IssuesEvent", "IssueCommentEvent", "PullRequestReviewEvent"})

stats = [
    ("Public repositories", profile.get("public_repos", 0)),
    ("Followers", profile.get("followers", 0)),
    ("Repository stars", total_stars),
    ("Public activity", contributions),
]
stats_body = ""
for index, (name, value) in enumerate(stats):
    x = 35 + (index % 2) * 465
    y = 90 + (index // 2) * 110
    stats_body += f'<rect x="{x}" y="{y}" width="430" height="82" rx="10" fill="#161b22" stroke="#30363d"/>'
    stats_body += label(x + 20, y + 32, name, 15, "#8b949e")
    stats_body += label(x + 20, y + 66, value, 25, "#f0f6fc", "700")
(OUT / "stats.svg").write_text(document("GitHub Statistics", stats_body, 335), encoding="utf-8")

language_totals = Counter()
for repo in repos:
    try:
        for language, amount in get(f"/repos/{repo['full_name']}/languages").items():
            language_totals[language] += amount
    except urllib.error.HTTPError:
        continue
languages = language_totals.most_common(8)
lang_body = ""
if languages:
    total = sum(value for _, value in languages)
    for index, (language, amount) in enumerate(languages):
        y = 90 + index * 32
        width = max(4, round(760 * amount / total))
        lang_body += label(35, y, language, 15)
        lang_body += f'<rect x="180" y="{y - 16}" width="{width}" height="18" rx="4" fill="#2f81f7"/>'
        lang_body += label(955, y, f"{amount / total:.1%}", 14, "#8b949e")
else:
    lang_body = label(35, 115, "No public language data is available yet.", 17, "#8b949e")
(OUT / "languages.svg").write_text(document("Most Used Languages", lang_body, max(150, 120 + len(languages) * 32)), encoding="utf-8")

# Use positive SVG bar heights. Negative rect heights render as empty SVGs.
by_day = Counter(event.get("created_at", "")[:10] for event in events if event.get("created_at"))
recent = sorted(by_day.items())[-30:]
activity_body = ""
if recent:
    max_count = max(count for _, count in recent)
    for index, (day, count) in enumerate(recent):
        height = max(8, round(185 * count / max_count))
        x = 35 + index * 30
        y = 280 - height
        activity_body += f'<rect x="{x}" y="{y}" width="18" height="{height}" rx="3" fill="#2f81f7"><title>{esc(day)}: {count} public events</title></rect>'
    activity_body += label(35, 325, "Public GitHub events from the latest API window", 14, "#8b949e")
else:
    activity_body = label(35, 145, "No recent public events were returned by GitHub.", 18, "#8b949e") + label(35, 180, "The graph will populate after new public activity.", 15, "#8b949e")
(OUT / "activity.svg").write_text(document("GitHub Activity Graph", activity_body, 360), encoding="utf-8")

# These are real calculated achievements, rather than incorrectly labeling profile totals as trophies.
achievements = [("Public repos", profile.get("public_repos", 0)), ("Followers", profile.get("followers", 0)), ("Stars earned", total_stars), ("Forks received", total_forks)]
trophy_body = ""
for index, (name, value) in enumerate(achievements):
    x = 35 + index * 235
    trophy_body += f'<rect x="{x}" y="90" width="205" height="155" rx="10" fill="#161b22" stroke="#30363d"/>'
    trophy_body += label(x + 20, 130, "ACHIEVEMENT", 12, "#f2cc60", "700")
    trophy_body += label(x + 20, 178, value, 28, "#f0f6fc", "700")
    trophy_body += label(x + 20, 215, name, 14, "#8b949e")
(OUT / "trophies.svg").write_text(document("GitHub Achievements", trophy_body, 285), encoding="utf-8")

# Rank by stars, then forks, then recent activity; this is transparent and reproducible.
top = sorted(repos, key=lambda repo: (repo.get("stargazers_count", 0), repo.get("forks_count", 0), repo.get("pushed_at", "")), reverse=True)[:5]
repo_body = ""
for index, repo in enumerate(top):
    y = 95 + index * 42
    repo_body += label(35, y, f"{index + 1}. {repo.get('name', 'repository')}", 17, "#58a6ff", "700")
    repo_body += label(450, y, f"stars: {repo.get('stargazers_count', 0)} • forks: {repo.get('forks_count', 0)}", 15, "#8b949e")
(OUT / "top-repositories.svg").write_text(document("Top Repositories", repo_body, max(150, 125 + len(top) * 42)), encoding="utf-8")

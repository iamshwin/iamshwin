"""Rewrite the README timeline from public GitHub activity. Standard library only."""
import json
import os
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

USER = "iamshwin"
README = Path(__file__).parent.parent / "README.md"
SKIP_REPOS = {USER, "dotfiles"}
REPO_NOTES = {"spoticron": "scheduled job that overwrote Spotify's Daily Drive playlist... because I didn't like their algorithm"}
# Upstream titles stay verbatim, except where a title means nothing out of context.
TITLE_OVERRIDES = {
    "https://github.com/phileasme/GitPeek/pull/1": "GitPeek browser extension, built at a GDG hackathon",
    "https://github.com/phileasme/GitPeek/pull/2": None,
}


def get(path):
    request = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def entries():
    query = urllib.parse.quote(f"author:{USER} type:pr is:merged is:public")
    for pr in get(f"search/issues?q={query}&per_page=100")["items"]:
        url = pr["html_url"]
        title = TITLE_OVERRIDES.get(url, pr["title"])
        if title is None:
            continue
        repo = pr["repository_url"].removeprefix("https://api.github.com/repos/")
        yield pr["pull_request"]["merged_at"][:10], f"[{repo}]({url}): {title}"
    for repo in get(f"users/{USER}/repos?per_page=100&type=owner"):
        if repo["fork"] or repo["private"] or repo["name"] in SKIP_REPOS:
            continue
        note = repo["description"] or REPO_NOTES.get(repo["name"], "my own project")
        yield repo["created_at"][:10], f"[{repo['name']}]({repo['html_url']}): {note}"


def render():
    by_year = defaultdict(list)
    for date, line in entries():
        by_year[date[:4]].append((date, line))
    blocks = []
    for year in sorted(by_year, reverse=True):
        lines = "\n".join(f"- {line}" for _, line in sorted(by_year[year], reverse=True))
        blocks.append(f"**{year}**\n{lines}")
    return "\n\n".join(blocks)


def main():
    pattern = r"(<!-- timeline:start -->\n).*?(<!-- timeline:end -->)"
    text = README.read_text()
    README.write_text(re.sub(pattern, lambda m: f"{m[1]}{render()}\n{m[2]}", text, flags=re.DOTALL))


if __name__ == "__main__":
    main()

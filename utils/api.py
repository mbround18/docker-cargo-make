import re
from typing import List, Set
import requests
from github import Github
from rich.console import Console
from .auth import get_github_token

console = Console()


def get_github_releases() -> List[str]:
    """Fetch all release tags from cargo-make GitHub repository."""
    try:
        token = get_github_token()
        g = Github(token) if token else Github()
        repo = g.get_repo("sagiegurari/cargo-make")
        releases = repo.get_releases()

        versions = []
        for release in releases:
            tag = release.tag_name
            if re.match(r"^\d+\.\d+\.\d+$", tag):
                versions.append(tag)

        return sorted(versions, key=lambda x: tuple(map(int, x.split("."))))
    except Exception as e:
        console.print(f"[red]Error fetching GitHub releases: {e}[/red]")
        return []


def get_docker_hub_tags() -> Set[str]:
    """Fetch existing tags from Docker Hub repository."""
    try:
        url = "https://hub.docker.com/v2/repositories/mbround18/cargo-make/tags"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        tags = set()

        while True:
            for tag_info in data.get("results", []):
                tag_name = tag_info["name"]
                if re.match(r"^\d+\.\d+\.\d+$", tag_name):
                    tags.add(tag_name)

            next_url = data.get("next")
            if not next_url:
                break

            response = requests.get(next_url)
            response.raise_for_status()
            data = response.json()

        return tags
    except Exception as e:
        console.print(f"[red]Error fetching Docker Hub tags: {e}[/red]")
        return set()

from typing import List, Set, Tuple
from .api import get_github_releases, get_docker_hub_tags
from rich.console import Console

console = Console()


def get_missing_versions() -> Tuple[List[str], Set[str], List[str]]:
    """Get GitHub versions, Docker Hub tags, and missing versions."""
    github_versions = get_github_releases()
    docker_tags = get_docker_hub_tags()
    missing_versions = [v for v in github_versions if v not in docker_tags]

    return github_versions, docker_tags, missing_versions


def get_baseline_version() -> str:
    """Get the earliest version that exists in Docker Hub to use as baseline."""
    docker_tags = get_docker_hub_tags()
    if not docker_tags:
        return "0.0.0"  # Default if no tags exist

    sorted_tags = sorted(docker_tags, key=lambda x: tuple(map(int, x.split("."))))
    baseline = sorted_tags[0]
    console.print(f"[blue]Using baseline version: {baseline}[/blue]")
    return baseline


def get_missing_versions_filtered() -> Tuple[List[str], Set[str], List[str]]:
    """Get GitHub versions, Docker Hub tags, and missing versions filtered by baseline."""
    github_versions = get_github_releases()
    docker_tags = get_docker_hub_tags()
    baseline_version = get_baseline_version()

    # Filter GitHub versions to only include those >= baseline
    baseline_tuple = tuple(map(int, baseline_version.split(".")))
    filtered_github_versions = [
        v for v in github_versions if tuple(map(int, v.split("."))) >= baseline_tuple
    ]

    missing_versions = [v for v in filtered_github_versions if v not in docker_tags]

    return filtered_github_versions, docker_tags, missing_versions


def get_extra_versions() -> List[str]:
    """Get versions that exist in Docker Hub but not in GitHub releases."""
    github_versions = get_github_releases()
    docker_tags = get_docker_hub_tags()
    extra_versions = [v for v in docker_tags if v not in github_versions]

    return sorted(extra_versions, key=lambda x: tuple(map(int, x.split("."))))

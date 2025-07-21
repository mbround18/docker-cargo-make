import re
import os
import subprocess
from typing import List, Set, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import docker
from docker.errors import ImageNotFound
import requests
from github import Github
from invoke.tasks import task
from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()


def get_github_token() -> Optional[str]:
    """Get GitHub token from environment or gh CLI."""
    # First try environment variable
    token = os.getenv("GITHUB_TOKEN")
    if token:
        console.print("[dim]Using GITHUB_TOKEN from environment[/dim]")
        return token

    # Try gh CLI
    try:
        result = subprocess.run(
            ["gh auth token"], capture_output=True, text=True, check=True, shell=True
        )
        token = result.stdout.strip()
        if token:
            console.print("[dim]Using token from gh CLI[/dim]")
            return token
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[dim]No gh CLI found or not authenticated[/dim]")

    console.print("[dim]No GitHub token found, using unauthenticated requests[/dim]")
    return None


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


def check_docker_daemon() -> bool:
    """Check if Docker daemon is running and accessible."""
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception as e:
        console.print(f"[red]Docker daemon not accessible: {e}[/red]")
        console.print(
            "[yellow]Make sure Docker is running and you have proper permissions[/yellow]"
        )
        return False


def build_and_push_image(version: str) -> Tuple[str, bool, str]:
    """Build and push Docker image for a specific version."""
    try:
        client = docker.from_env()
        image_tag = f"mbround18/cargo-make:{version}"

        console.print(f"[blue]Building {image_tag}...[/blue]")

        image, logs = client.images.build(
            path=".",
            tag=image_tag,
            buildargs={"CARGO_MAKE_VERSION": version.replace("v", "")},
            rm=True,
        )

        console.print(f"[blue]Pushing {image_tag}...[/blue]")

        for line in client.images.push(image_tag, stream=True, decode=True):
            if "error" in line:
                raise Exception(line["error"])

        console.print(f"[green]Successfully built and pushed {image_tag}[/green]")
        return version, True, "Success"

    except Exception as e:
        error_msg = str(e)
        if (
            "Connection aborted" in error_msg
            or "No such file or directory" in error_msg
        ):
            error_msg = "Docker daemon not running or accessible"
        console.print(f"[red]Failed to build/push {version}: {error_msg}[/red]")
        return version, False, error_msg


def yank_docker_image(version: str) -> Tuple[str, bool, str]:
    """Remove Docker image tag from local Docker and attempt cleanup."""
    try:
        client = docker.from_env()
        image_tag = f"mbround18/cargo-make:{version}"

        console.print(f"[yellow]Yanking local image {image_tag}...[/yellow]")

        try:
            client.images.remove(image_tag, force=True)
        except ImageNotFound:
            pass

        console.print(f"[green]Successfully yanked local image {image_tag}[/green]")
        return version, True, "Yanked from local"

    except Exception as e:
        error_msg = str(e)
        console.print(f"[red]Failed to yank {version}: {error_msg}[/red]")
        return version, False, error_msg


@task
def diff(c, baseline=None):
    """Show the difference between GitHub releases and Docker Hub tags."""
    console.print("[bold blue]Checking version differences...[/bold blue]")

    if baseline:
        console.print(f"[blue]Using manual baseline version: {baseline}[/blue]")
        # Override the baseline for this run
        original_func = get_baseline_version
        globals()["get_baseline_version"] = lambda: baseline
        github_versions, docker_tags, missing_versions = get_missing_versions_filtered()
        globals()["get_baseline_version"] = original_func
    else:
        github_versions, docker_tags, missing_versions = get_missing_versions_filtered()

    table = Table(title="Version Comparison")
    table.add_column("Version", style="cyan")
    table.add_column("GitHub", style="green")
    table.add_column("Docker Hub", style="yellow")
    table.add_column("Status", style="bold")

    all_versions = sorted(
        set(github_versions) | docker_tags, key=lambda x: tuple(map(int, x.split(".")))
    )

    for version in all_versions:
        in_github = "✓" if version in github_versions else "✗"
        in_docker = "✓" if version in docker_tags else "✗"

        if version in missing_versions:
            status = Text("Missing", style="red bold")
        elif version in github_versions and version in docker_tags:
            status = Text("Synced", style="green")
        elif version not in github_versions and version in docker_tags:
            status = Text("Extra", style="yellow")
        else:
            status = Text("Unknown", style="dim")

        table.add_row(version, in_github, in_docker, status)

    console.print(table)

    if missing_versions:
        console.print(
            f"\n[red bold]{len(missing_versions)} versions missing from Docker Hub[/red bold]"
        )
    else:
        console.print("\n[green bold]All versions are synced! 🎉[/green bold]")


@task
def sync(c, replace=None):
    """Sync missing Docker images with GitHub releases.

    Args:
        replace: Either 'all' to resync all versions, or a specific version to resync
    """
    console.print("[bold blue]Starting sync process...[/bold blue]")

    # Check Docker daemon first
    if not check_docker_daemon():
        console.print("[red]Cannot proceed without Docker daemon. Exiting.[/red]")
        return

    github_versions, docker_tags, missing_versions = get_missing_versions_filtered()

    # Handle replace flag
    if replace:
        if replace.lower() == "all":
            console.print("[yellow]Replace mode: Resyncing ALL versions[/yellow]")
            versions_to_build = github_versions
        else:
            if replace in github_versions:
                console.print(
                    f"[yellow]Replace mode: Resyncing version {replace}[/yellow]"
                )
                versions_to_build = [replace]
            else:
                console.print(
                    f"[red]Version {replace} not found in GitHub releases[/red]"
                )
                return
    else:
        versions_to_build = missing_versions
        if not missing_versions:
            console.print("[green]All versions are already synced! 🎉[/green]")
            return
        console.print(
            f"[yellow]Found {len(missing_versions)} missing versions to build[/yellow]"
        )

    if replace:
        console.print(
            f"[yellow]Building {len(versions_to_build)} version(s) in replace mode[/yellow]"
        )
    else:
        console.print(
            f"[yellow]Found {len(missing_versions)} missing versions to build[/yellow]"
        )

    results = []
    failed_builds = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_version = {
            executor.submit(build_and_push_image, version): version
            for version in versions_to_build
        }

        for future in as_completed(future_to_version):
            version, success, message = future.result()
            results.append((version, success, message))

            if not success:
                failed_builds.append(version)

    console.print("\n[bold blue]Build Summary:[/bold blue]")

    table = Table()
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Message")

    for version, success, message in sorted(results):
        status = (
            Text("✓ Success", style="green")
            if success
            else Text("✗ Failed", style="red")
        )
        table.add_row(version, status, message)

    console.print(table)

    successful_builds = len([r for r in results if r[1]])
    if replace:
        console.print(
            f"\n[green]Successfully rebuilt {successful_builds}/{len(versions_to_build)} images[/green]"
        )
    else:
        console.print(
            f"\n[green]Successfully built {successful_builds}/{len(missing_versions)} images[/green]"
        )

    if failed_builds:
        console.print(f"[red]Failed builds: {', '.join(failed_builds)}[/red]")

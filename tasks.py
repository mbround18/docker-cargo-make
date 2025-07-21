from concurrent.futures import ThreadPoolExecutor, as_completed
from invoke.tasks import task
from rich.console import Console
from rich.table import Table
from rich.text import Text

from utils.config import load_skip_config, should_skip_version
from utils.version_compare import get_missing_versions_filtered, get_baseline_version
from utils.docker_ops import check_docker_daemon, build_and_push_image

console = Console()


@task
def diff(c, baseline=None):
    """Show the difference between GitHub releases and Docker Hub tags."""
    console.print("[bold blue]Checking version differences...[/bold blue]")

    skip_config = load_skip_config()

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
    table.add_column("Notes", style="dim")

    all_versions = sorted(
        set(github_versions) | docker_tags, key=lambda x: tuple(map(int, x.split(".")))
    )

    for version in all_versions:
        in_github = "✓" if version in github_versions else "✗"
        in_docker = "✓" if version in docker_tags else "✗"

        should_skip, skip_reason = should_skip_version(version, skip_config)
        notes = skip_reason if should_skip else ""

        if should_skip:
            status = Text("Skipped", style="yellow bold")
        elif version in missing_versions:
            status = Text("Missing", style="red bold")
        elif version in github_versions and version in docker_tags:
            status = Text("Synced", style="green")
        elif version not in github_versions and version in docker_tags:
            status = Text("Extra", style="yellow")
        else:
            status = Text("Unknown", style="dim")

        table.add_row(version, in_github, in_docker, status, notes)

    console.print(table)

    # Count skipped versions
    skipped_versions = [
        v for v in github_versions if should_skip_version(v, skip_config)[0]
    ]
    available_missing = [
        v for v in missing_versions if not should_skip_version(v, skip_config)[0]
    ]

    if skipped_versions:
        console.print(
            f"\n[yellow]{len(skipped_versions)} versions skipped due to configuration[/yellow]"
        )

    if available_missing:
        console.print(
            f"\n[red bold]{len(available_missing)} versions missing from Docker Hub (excluding skipped)[/red bold]"
        )
    elif not missing_versions:
        console.print("\n[green bold]All versions are synced! 🎉[/green bold]")
    else:
        console.print(
            "\n[green bold]All available versions are synced! 🎉[/green bold]"
        )


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

    skip_config = load_skip_config()
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

    # Filter out skipped versions and track them
    skipped_versions = []
    filtered_versions = []

    for version in versions_to_build:
        should_skip, skip_reason = should_skip_version(version, skip_config)
        if should_skip:
            skipped_versions.append((version, skip_reason))
        else:
            filtered_versions.append(version)

    versions_to_build = filtered_versions

    # Show what we're going to do
    if replace:
        console.print(
            f"[yellow]Building {len(versions_to_build)} version(s) in replace mode[/yellow]"
        )
    else:
        console.print(
            f"[yellow]Found {len(missing_versions)} missing versions, building {len(versions_to_build)} (excluding skipped)[/yellow]"
        )

    # Show skipped versions if any
    if skipped_versions:
        console.print(f"[yellow]Skipping {len(skipped_versions)} version(s):[/yellow]")
        for version, reason in skipped_versions:
            console.print(f"  [dim]{version}: {reason}[/dim]")

    if not versions_to_build:
        console.print("[green]No versions to build after filtering! 🎉[/green]")
        return

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

    # Add build results
    for version, success, message in sorted(results):
        status = (
            Text("✓ Success", style="green")
            if success
            else Text("✗ Failed", style="red")
        )
        table.add_row(version, status, message)

    # Add skipped versions to the summary table
    for version, skip_reason in sorted(skipped_versions):
        status = Text("⚠ Skipped", style="yellow")
        table.add_row(version, status, skip_reason)

    console.print(table)

    successful_builds = len([r for r in results if r[1]])

    if replace:
        console.print(
            f"\n[green]Successfully rebuilt {successful_builds}/{len(versions_to_build)} images[/green]"
        )
    else:
        console.print(
            f"\n[green]Successfully built {successful_builds}/{len(versions_to_build)} images[/green]"
        )

    if skipped_versions:
        console.print(
            f"[yellow]Skipped {len(skipped_versions)} version(s) due to configuration[/yellow]"
        )

    if failed_builds:
        console.print(f"[red]Failed builds: {', '.join(failed_builds)}[/red]")

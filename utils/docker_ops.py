from typing import Tuple
import docker
from docker.errors import ImageNotFound
from rich.console import Console

console = Console()


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

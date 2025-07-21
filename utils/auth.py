import os
import subprocess
from typing import Optional
from rich.console import Console

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

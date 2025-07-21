import os
import json
from typing import Dict, Tuple
from rich.console import Console

console = Console()


def load_skip_config() -> Dict[str, str]:
    """Load skip configuration from config/skip.json."""
    try:
        config_path = os.path.join("config", "skip.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                skip_config = json.load(f)
                console.print(
                    f"[dim]Loaded skip config with {len(skip_config)} entries[/dim]"
                )
                return skip_config
        else:
            console.print("[dim]No skip config found at config/skip.json[/dim]")
            return {}
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load skip config: {e}[/yellow]")
        return {}


def should_skip_version(version: str, skip_config: Dict[str, str]) -> Tuple[bool, str]:
    """Check if a version should be skipped and return the reason."""
    if version in skip_config:
        return True, skip_config[version]
    return False, ""

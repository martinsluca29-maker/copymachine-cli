import base64
import requests
from rich.console import Console
from .config import get_config, save_config

API_BASE = "https://app.getcopymachine.com"
console = Console()


def _encode_key(key: str) -> str:
    return base64.b64encode(key.encode()).decode()


def _decode_key(encoded: str) -> str:
    return base64.b64decode(encoded.encode()).decode()


def get_saved_key() -> str | None:
    config = get_config()
    encoded = config.get("cli_key")
    if encoded:
        return _decode_key(encoded)
    return None


def save_key(key: str) -> None:
    save_config({"cli_key": _encode_key(key)})


def validate_key(key: str) -> bool:
    try:
        resp = requests.post(
            f"{API_BASE}/api/validate-cli-key",
            headers={"X-CLI-Key": key},
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException:
        return False


def prompt_and_save_key() -> str:
    console.print("\n[bold cyan]Enter your CLI key[/bold cyan] (found in Copy Machine → Settings → CLI Access):")
    key = input("  Key: ").strip()

    if not key:
        console.print("[red]No key entered. Exiting.[/red]")
        raise SystemExit(1)

    console.print("[dim]Validating key...[/dim]")
    if not validate_key(key):
        console.print(
            "[red]Invalid key. Check your Settings page at app.getcopymachine.com[/red]"
        )
        raise SystemExit(1)

    save_key(key)
    console.print("[green]Key saved.[/green]")
    return key


def ensure_key() -> str:
    key = get_saved_key()
    if key:
        return key
    return prompt_and_save_key()

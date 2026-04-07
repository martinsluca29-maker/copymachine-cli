import platform
import subprocess
import sys

from rich.console import Console

console = Console()


def is_ffmpeg_installed() -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _install_windows() -> bool:
    console.print("[dim]Running: winget install ffmpeg[/dim]")
    result = subprocess.run(["winget", "install", "ffmpeg"], check=False)
    return result.returncode == 0


def _install_mac() -> bool:
    console.print("[dim]Running: brew install ffmpeg[/dim]")
    result = subprocess.run(["brew", "install", "ffmpeg"], check=False)
    return result.returncode == 0


def _install_linux() -> bool:
    console.print("[dim]Running: apt install ffmpeg -y[/dim]")
    result = subprocess.run(["apt", "install", "ffmpeg", "-y"], check=False)
    return result.returncode == 0


def _print_manual_instructions() -> None:
    console.print(
        "\n[yellow]Automatic install failed. Please install FFmpeg manually:[/yellow]\n"
        "  Windows : https://ffmpeg.org/download.html  (or: winget install ffmpeg)\n"
        "  Mac     : brew install ffmpeg\n"
        "  Linux   : sudo apt install ffmpeg\n"
        "\nThen re-run [bold]copymachine[/bold]."
    )


def ensure_ffmpeg() -> None:
    if is_ffmpeg_installed():
        return

    console.print("[yellow]FFmpeg not found.[/yellow]")
    answer = input("Install FFmpeg automatically? [Y/n]: ").strip().lower()
    if answer in ("n", "no"):
        _print_manual_instructions()
        sys.exit(1)

    system = platform.system()
    success = False

    if system == "Windows":
        success = _install_windows()
    elif system == "Darwin":
        success = _install_mac()
    elif system == "Linux":
        success = _install_linux()
    else:
        console.print(f"[red]Unsupported platform: {system}[/red]")

    if not success or not is_ffmpeg_installed():
        _print_manual_instructions()
        sys.exit(1)

    console.print("[green]FFmpeg installed successfully.[/green]")

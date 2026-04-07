import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from .api import download_pack, fetch_ready_jobs
from .assembly import assemble
from .auth import ensure_key
from .config import get_output_folder, set_output_folder
from .installer import ensure_ffmpeg

console = Console()

BORDER = "═" * 38


def _format_expiry(expires_at: str | None) -> str:
    if not expires_at:
        return "unknown"
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = exp - now
        if delta.total_seconds() <= 0:
            return "expired"
        days = delta.days
        hours = delta.seconds // 3600
        return f"{days}d {hours}h"
    except Exception:
        return expires_at


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def _ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    hint = "[Y/n]" if default_yes else "[y/N]"
    raw = input(f"  {prompt} {hint}: ").strip().lower()
    if raw == "":
        return default_yes
    return raw in ("y", "yes")


def _print_header() -> None:
    console.print()
    console.print(BORDER)
    console.print(" COPY MACHINE CLI")
    console.print(BORDER)


def _print_job_menu(jobs: list[dict]) -> None:
    console.print(" Ready to assemble:\n")
    for i, job in enumerate(jobs, start=1):
        name = job.get("name", f"Job {job['id']}")
        image_count = job.get("image_count", "?")
        duration_min = job.get("duration_minutes", "?")
        expires_in = _format_expiry(job.get("expires_at"))
        console.print(f" [{i}] {name}")
        console.print(f"     {image_count} images · {duration_min} min · expires in {expires_in}\n")
    console.print(" [A] Assemble all")
    console.print(" [Q] Quit")
    console.print(BORDER)


def _assemble_job(job: dict, key: str) -> None:
    name = job.get("name", f"Job {job['id']}")
    console.print(f'\n Assemble "[bold]{name}[/bold]"?\n')

    use_crossfade = _ask_yes_no("Transitions: crossfade 0.3s", default_yes=True)
    use_zoom = _ask_yes_no("Zoom IN effect: slow Ken Burns", default_yes=True)
    use_captions = _ask_yes_no("Captions: burn in subtitles", default_yes=False)

    default_folder = get_output_folder()
    raw_folder = input(f"  Output folder [{default_folder}]: ").strip()
    output_folder = Path(raw_folder) if raw_folder else Path(default_folder)

    if raw_folder:
        set_output_folder(raw_folder)

    pack_dir = download_pack(job["id"], key)

    slug = _slugify(name)
    output_path = output_folder / f"{slug}.mp4"

    try:
        assemble(
            pack_dir=pack_dir,
            output_path=output_path,
            zoom=use_zoom,
            crossfade=use_crossfade,
            captions=use_captions,
        )
    finally:
        shutil.rmtree(pack_dir.parent, ignore_errors=True)

    duration = _get_mp4_duration(output_path)
    console.print(f"\n[green]Done![/green] {output_path.name} ({duration})\n")


def _get_mp4_duration(path: Path) -> str:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True, text=True, check=True,
        )
        secs = float(result.stdout.strip())
        m, s = divmod(int(secs), 60)
        return f"{m}m {s:02d}s"
    except Exception:
        return "?"


def main() -> None:
    ensure_ffmpeg()
    key = ensure_key()

    while True:
        _print_header()

        console.print("[dim]Fetching jobs...[/dim]")
        try:
            jobs = fetch_ready_jobs(key)
        except Exception as exc:
            console.print(f"[red]Failed to fetch jobs: {exc}[/red]")
            return

        if not jobs:
            console.print("\n [yellow]No jobs ready for assembly yet.[/yellow]")
            console.print(" Generate some videos at app.getcopymachine.com")
            console.print(" and come back when they show 'CLI Ready' status.\n")
            input(" Press Enter to exit.")
            return

        _print_job_menu(jobs)
        choice = input(" Choose: ").strip().lower()

        if choice == "q":
            break

        if choice == "a":
            for job in jobs:
                _assemble_job(job, key)
            continue

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(jobs):
                _assemble_job(jobs[idx], key)
            else:
                console.print("[red]Invalid selection.[/red]")
        else:
            console.print("[red]Invalid selection.[/red]")

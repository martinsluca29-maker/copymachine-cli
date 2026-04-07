import os
import tempfile
import zipfile
from pathlib import Path

import requests
from rich.console import Console
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

API_BASE = "https://app.getcopymachine.com"
console = Console()


def fetch_ready_jobs(key: str) -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/jobs",
        headers={"X-CLI-Key": key},
        timeout=15,
    )
    resp.raise_for_status()
    jobs = resp.json()
    return [j for j in jobs if j.get("status") == "ready_for_cli"]


def download_pack(job_id: str, key: str) -> Path:
    """Download and extract a job pack. Returns the extraction directory."""
    console.print(f"\n[cyan]Downloading pack...[/cyan]")

    resp = requests.post(
        f"{API_BASE}/api/jobs/{job_id}/download-pack",
        headers={"X-CLI-Key": key},
        stream=True,
        timeout=60,
    )
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    tmp_dir = Path(tempfile.mkdtemp(prefix="copymachine_"))
    zip_path = tmp_dir / "pack.zip"

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading", total=total if total else None)
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                progress.advance(task, len(chunk))

    console.print("[dim]Extracting...[/dim]")
    extract_dir = tmp_dir / "pack"
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    zip_path.unlink()

    return extract_dir

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

console = Console()

FPS = 25
ZOOM_SPEED = 0.0015   # per-frame zoom increment → reaches 1.1x in ~67 frames
MAX_ZOOM = 1.1
CROSSFADE_DURATION = 0.3  # seconds


def _load_manifest(pack_dir: Path) -> dict:
    manifest_path = pack_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return {}


def _sorted_images(pack_dir: Path) -> list[Path]:
    images_dir = pack_dir / "images"
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    images = sorted(
        [p for p in images_dir.iterdir() if p.suffix.lower() in exts],
        key=lambda p: p.name,
    )
    return images


def _get_audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def _build_zoompan_clip(image_path: Path, duration_sec: float, output_path: Path) -> None:
    """Render a single Ken-Burns zoomed clip from one image."""
    d_frames = int(duration_sec * FPS)
    zoompan = (
        f"zoompan=z='min(zoom+{ZOOM_SPEED},{MAX_ZOOM})':"
        f"d={d_frames}:"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"s=1920x1080"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", f"scale=1920x1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,{zoompan}",
        "-t", str(duration_sec),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def _concat_with_crossfade(clip_paths: list[Path], output_path: Path, duration_sec: float) -> None:
    """Concatenate clips with xfade crossfade transitions."""
    if len(clip_paths) == 1:
        shutil.copy(clip_paths[0], output_path)
        return

    # Build complex filter for chained xfade
    inputs = []
    for p in clip_paths:
        inputs += ["-i", str(p)]

    # Each clip contributes (duration - crossfade) seconds before the next fade starts
    offset = duration_sec - CROSSFADE_DURATION

    filter_parts = []
    current = "[0:v]"
    for i in range(1, len(clip_paths)):
        next_label = f"[v{i}]" if i < len(clip_paths) - 1 else "[vout]"
        t = round(offset * i, 4)
        filter_parts.append(
            f"{current}[{i}:v]xfade=transition=fade:duration={CROSSFADE_DURATION}:offset={t}{next_label}"
        )
        current = f"[v{i}]"

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def _merge_audio(video_path: Path, audio_path: Path, output_path: Path) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_path),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def _burn_captions(video_path: Path, script_path: Path, output_path: Path) -> None:
    drawtext = (
        f"drawtext=textfile='{script_path}':"
        "fontcolor=white:fontsize=36:"
        "x=(w-text_w)/2:y=h*0.8:"
        "box=1:boxcolor=black@0.4:boxborderw=6"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", drawtext,
        "-c:a", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def assemble(
    pack_dir: Path,
    output_path: Path,
    zoom: bool = True,
    crossfade: bool = True,
    captions: bool = False,
) -> None:
    audio_path = pack_dir / "audio.mp3"
    script_path = pack_dir / "script.txt"
    images = _sorted_images(pack_dir)

    if not images:
        raise RuntimeError(f"No images found in {pack_dir / 'images'}")
    if not audio_path.exists():
        raise RuntimeError(f"audio.mp3 not found in {pack_dir}")

    audio_duration = _get_audio_duration(audio_path)
    clip_duration = audio_duration / len(images)

    work_dir = Path(tempfile.mkdtemp(prefix="cm_assembly_"))

    try:
        clip_paths: list[Path] = []

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Rendering clips", total=len(images)
            )

            for i, img in enumerate(images):
                clip_out = work_dir / f"clip_{i:05d}.mp4"
                if zoom:
                    _build_zoompan_clip(img, clip_duration, clip_out)
                else:
                    # Static clip without zoom
                    d_frames = int(clip_duration * FPS)
                    cmd = [
                        "ffmpeg", "-y",
                        "-loop", "1",
                        "-i", str(img),
                        "-vf", "scale=1920x1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
                        "-t", str(clip_duration),
                        "-r", str(FPS),
                        "-c:v", "libx264",
                        "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        str(clip_out),
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                clip_paths.append(clip_out)
                progress.advance(task)

        console.print("[dim]Joining clips...[/dim]")
        joined_path = work_dir / "joined.mp4"

        if crossfade and len(clip_paths) > 1:
            _concat_with_crossfade(clip_paths, joined_path, clip_duration)
        else:
            # Simple concat via list file
            list_file = work_dir / "clips.txt"
            with open(list_file, "w") as f:
                for p in clip_paths:
                    f.write(f"file '{p}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                str(joined_path),
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        console.print("[dim]Merging audio...[/dim]")
        with_audio = work_dir / "with_audio.mp4"
        _merge_audio(joined_path, audio_path, with_audio)

        final = with_audio
        if captions and script_path.exists():
            console.print("[dim]Burning captions...[/dim]")
            captioned = work_dir / "captioned.mp4"
            _burn_captions(with_audio, script_path, captioned)
            final = captioned

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(final, output_path)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

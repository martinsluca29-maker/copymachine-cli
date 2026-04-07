# Copy Machine CLI

Assemble your AI-generated videos locally.

## Install

```bash
pip install copymachine-cli
```

## Setup

1. Get your CLI key from [app.getcopymachine.com](https://app.getcopymachine.com/app)
   → Settings → CLI Access → Generate Key
2. Run: `copymachine`
3. Enter your key when prompted
4. Select jobs to assemble

## Requirements

- Python 3.9+
- FFmpeg (auto-installed on first run)
- Copy Machine account (Creator plan or above)

## Usage

Run `copymachine` from any terminal. You'll see a menu of your ready-to-assemble jobs:

```
══════════════════════════════════════
 COPY MACHINE CLI
══════════════════════════════════════
 Ready to assemble:

 [1] Pine Tar History
     277 images · 25 min · expires in 6d 14h

 [2] Cold War Secrets
     158 images · 14 min · expires in 5d 2h

 [A] Assemble all
 [Q] Quit
══════════════════════════════════════
 Choose:
```

Per job you'll be prompted for:

- **Crossfade transitions** — smooth 0.3s fade between images (recommended)
- **Ken Burns zoom** — slow cinematic zoom-in effect (recommended)
- **Captions** — burn subtitles from script into video
- **Output folder** — where to save the final MP4

## How it works

1. Downloads your image pack (images + audio + manifest) as a ZIP from the Copy Machine cloud
2. Renders each image into a short clip with optional Ken Burns zoom using FFmpeg
3. Joins clips with optional crossfade transitions
4. Merges the audio track
5. Optionally burns in captions
6. Saves the final MP4 to your chosen folder

## Config

Your CLI key and output folder preference are saved to `~/.copymachine/config.json`.

To reset your key, delete that file and run `copymachine` again.

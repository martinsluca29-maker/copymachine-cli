import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".copymachine"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = get_config()
    existing.update(data)
    with open(CONFIG_FILE, "w") as f:
        json.dump(existing, f, indent=2)


def get_output_folder() -> str:
    config = get_config()
    if "output_folder" in config:
        return config["output_folder"]
    return str(Path.home() / "Videos")


def set_output_folder(folder: str) -> None:
    save_config({"output_folder": folder})

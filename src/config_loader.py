"""
Load and validate configuration from config.yaml and .env.
"""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def get_project_root() -> Path:
    return _PROJECT_ROOT


def load_config() -> dict:
    config_path = _PROJECT_ROOT / "config" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def get_path(key: str, config: dict = None) -> Path:
    if config is None:
        config = load_config()
    rel = config["paths"][key]
    return _PROJECT_ROOT / rel


def get_instagram_credentials() -> tuple[str, str]:
    user = os.getenv("INSTAGRAM_USERNAME", "").strip()
    pwd = os.getenv("INSTAGRAM_PASSWORD", "").strip()
    return user, pwd

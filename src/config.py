"""Configuration handler."""
from pathlib import Path

from dynaconf import Dynaconf

ROOT_DIR = Path(__file__).parents[1]

settings = Dynaconf(
    envvar_prefix="SOCIAL_MEDIA_CRON",
    settings_files=[ROOT_DIR / "settings.toml", ROOT_DIR / ".secrets.toml"],
)

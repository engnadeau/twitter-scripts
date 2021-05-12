from dynaconf import Dynaconf
from pathlib import Path

ROOT_DIR = Path(__file__).parents[1]

settings = Dynaconf(
    envvar_prefix="PERSONAL_CRON",
    settings_files=[ROOT_DIR / "settings.toml", ROOT_DIR / ".secrets.toml"],
)

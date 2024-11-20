from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = APP_ROOT / "data"
CONFIG_PATH = DATA_DIR / "app_config.json"


@dataclass
class AppSettings:
    employee_limit: int = 500
    default_sample_data: bool = True
    host: str = "127.0.0.1"
    port: int = 8765


def load_settings() -> AppSettings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        settings = AppSettings()
        save_settings(settings)
        return settings

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}

    return AppSettings(
        employee_limit=int(data.get("employee_limit", 500)),
        default_sample_data=bool(data.get("default_sample_data", True)),
        host=str(data.get("host", "127.0.0.1")),
        port=int(data.get("port", 8765)),
    )


def save_settings(settings: AppSettings) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(settings.__dict__, indent=2),
        encoding="utf-8",
    )

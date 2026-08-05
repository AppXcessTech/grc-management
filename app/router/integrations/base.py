import json
from pathlib import Path

CONFIG_DIR = Path("data/integrations")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def config_path(org_id: int, provider: str) -> Path:
    provider_dir = CONFIG_DIR / provider
    provider_dir.mkdir(parents=True, exist_ok=True)
    return provider_dir / f"org_{org_id}.json"


def load_config(org_id: int, provider: str) -> dict:
    path = config_path(org_id, provider)
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_config(org_id: int, provider: str, data: dict):
    path = config_path(org_id, provider)
    path.write_text(json.dumps(data, indent=2))

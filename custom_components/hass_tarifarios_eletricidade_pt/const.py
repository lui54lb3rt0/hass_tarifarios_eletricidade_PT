"""Constants for the Tarifários Eletricidade PT integration."""
import json
from pathlib import Path

DOMAIN = "hass_tarifarios_eletricidade_pt"

def get_version():
    """Get version from manifest.json."""
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest.get("version", "unknown")
    except Exception:
        return "unknown"

VERSION = get_version()

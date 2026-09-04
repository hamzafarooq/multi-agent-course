from pathlib import Path

import yaml

from .config import ROOT


def load_videos() -> list[dict]:
    with open(ROOT / "videos.yaml") as f:
        return yaml.safe_load(f)["videos"]

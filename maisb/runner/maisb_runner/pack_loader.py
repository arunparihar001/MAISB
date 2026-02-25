"""Pack loader for MAISB scenario packs."""
import hashlib
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml


PACK_DIR = Path(__file__).parent.parent.parent / "packs"


def load_pack(version: str = "v3") -> Dict[str, Any]:
    """Load a scenario pack by version string (e.g. 'v3')."""
    pack_path = PACK_DIR / version
    if not pack_path.exists():
        raise FileNotFoundError(f"Pack directory not found: {pack_path}")

    metadata = load_metadata(pack_path)
    scenarios = load_scenarios(pack_path / "scenarios")
    pack_hash = compute_pack_hash(pack_path)

    return {
        "metadata": metadata,
        "scenarios": scenarios,
        "pack_hash": pack_hash,
        "pack_version": metadata.get("version", version),
    }


def load_metadata(pack_path: Path) -> dict:
    """Load pack metadata.yaml."""
    meta_file = pack_path / "metadata.yaml"
    if not meta_file.exists():
        return {}
    with open(meta_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_scenarios(scenarios_dir: Path) -> List[dict]:
    """Load all scenario YAML files from a directory, sorted by id."""
    if not scenarios_dir.exists():
        return []
    scenarios = []
    for yaml_file in sorted(scenarios_dir.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data:
                scenarios.append(data)
    # Sort by id for determinism
    scenarios.sort(key=lambda s: s.get("id", ""))
    return scenarios


def compute_pack_hash(pack_path: Path) -> str:
    """Compute SHA-256 hash over sorted scenario file contents + metadata."""
    hasher = hashlib.sha256()
    files = sorted((pack_path / "scenarios").glob("*.yaml")) if (pack_path / "scenarios").exists() else []
    meta_file = pack_path / "metadata.yaml"
    all_files = list(files) + ([meta_file] if meta_file.exists() else [])
    for f in sorted(str(p) for p in all_files):
        with open(f, "rb") as fh:
            hasher.update(fh.read())
    return hasher.hexdigest()


def get_quick_subset(scenarios: List[dict], n: int = 30) -> List[dict]:
    """Return the first n scenarios sorted by id (deterministic subset)."""
    sorted_scenarios = sorted(scenarios, key=lambda s: s.get("id", ""))
    return sorted_scenarios[:n]

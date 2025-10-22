"""Artifact manifest management."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass
class Manifest:
    """Manifest for model artifacts."""

    version: str
    model_path: str
    emb_path: str
    ann_path: str
    ann_backend: str
    embedding_dim: int
    covis_path: str
    brandpop_path: str
    catalog_checksum: Optional[str] = None
    created_at: Optional[str] = None


def write_manifest(path: str, manifest: Manifest) -> None:
    """
    Write manifest to JSON file.

    Args:
        path: Directory path to write manifest
        manifest: Manifest object
    """
    manifest_path = os.path.join(path, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(asdict(manifest), f, indent=2)


def read_manifest(path: str) -> Manifest:
    """
    Read manifest from JSON file.

    Args:
        path: Directory path containing manifest

    Returns:
        Manifest object
    """
    manifest_path = os.path.join(path, "manifest.json")
    with open(manifest_path, "r") as f:
        data = json.load(f)
    return Manifest(**data)


def compute_file_checksum(filepath: str) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        filepath: Path to file

    Returns:
        Hex digest of checksum
    """
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


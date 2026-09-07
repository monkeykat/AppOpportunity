"""Explicit before/after integrity checks for the Phase 1 boundary."""

import hashlib
from pathlib import Path
from typing import Dict, Iterable


def snapshot_files(paths: Iterable[Path]) -> Dict[str, str]:
    """Return SHA-256 hashes for explicitly supplied files and directories."""
    snapshot: Dict[str, str] = {}
    for supplied_path in paths:
        path = Path(supplied_path).resolve()
        candidates = sorted(path.rglob("*") if path.is_dir() else [path])
        for candidate in candidates:
            if not candidate.is_file():
                continue
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            snapshot[str(candidate)] = digest
    return snapshot


def assert_unchanged(before: Dict[str, str], paths: Iterable[Path]) -> None:
    """Raise an assertion with changed, added, or removed paths."""
    after = snapshot_files(paths)
    changed = sorted(
        path for path in set(before) | set(after) if before.get(path) != after.get(path)
    )
    if changed:
        raise AssertionError("Protected files changed: {}".format(", ".join(changed)))
from __future__ import annotations

import json
import re
import shutil
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from partpipeline.types import BatchManifest, RunManifest, RunPaths


def create_run_paths(
    input_path: Path,
    output_root: Path,
    timestamp: str | None = None,
) -> RunPaths:
    stamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = output_root.expanduser().resolve() / f"{_safe_stem(input_path)}-{stamp}"
    logs_dir = run_dir / "logs"
    sam_dir = run_dir / "sam"
    bridge_dir = run_dir / "bridge"
    prepared_dir = run_dir / "prepared"
    holopart_dir = run_dir / "holopart"

    for directory in (logs_dir, sam_dir, bridge_dir, prepared_dir, holopart_dir):
        directory.mkdir(parents=True, exist_ok=True)

    return RunPaths(
        run_dir=run_dir,
        logs_dir=logs_dir,
        sam_dir=sam_dir,
        bridge_dir=bridge_dir,
        prepared_dir=prepared_dir,
        holopart_dir=holopart_dir,
        manifest_path=run_dir / "manifest.json",
    )


def copy_selected_mask(source: Path, sam_dir: Path) -> Path:
    if not source.exists():
        raise FileNotFoundError(f"Selected SAMPart3D mask does not exist: {source}")
    sam_dir.mkdir(parents=True, exist_ok=True)
    destination = sam_dir / source.name
    shutil.copy2(source, destination)
    return destination


def bridge_artifact_paths(paths: RunPaths, mask_scale: str) -> dict[str, Path]:
    return {
        "prepared_glb": paths.bridge_dir / "prepared_parts.glb",
        "merged_mask": paths.bridge_dir / f"mesh_{mask_scale}_merged.npy",
        "part_manifest": paths.bridge_dir / "part_manifest.json",
    }


def create_batch_dir(output_root: Path, timestamp: str | None = None) -> Path:
    stamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    batch_dir = output_root.expanduser().resolve() / "batches" / f"batch-{stamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    return batch_dir


def write_manifest(manifest: RunManifest) -> Path:
    manifest.paths.manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest.paths.manifest_path


def write_batch_manifest(manifest: BatchManifest) -> Path:
    manifest.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest.manifest_path


def update_manifest_status(manifest: RunManifest, status: str) -> RunManifest:
    updated = replace(
        manifest,
        status=status,
        updated_at=datetime.now().isoformat(timespec="seconds"),
    )
    write_manifest(updated)
    return updated


def _safe_stem(path: Path) -> str:
    stem = path.stem.strip().lower()
    stem = re.sub(r"[^a-z0-9._-]+", "-", stem)
    stem = stem.strip("-._")
    return stem or "asset"

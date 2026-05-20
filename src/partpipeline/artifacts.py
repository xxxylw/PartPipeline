from __future__ import annotations

import json
import re
import shutil
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from partpipeline.types import (
    AnimationManifest,
    BatchManifest,
    PartExportManifest,
    PresentationBatchManifest,
    PresentationPackageManifest,
    RunManifest,
    RunPaths,
)


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


def create_presentation_package_dir(
    presentation_root: Path,
    run_dir: Path,
    input_path: Path | None = None,
) -> Path:
    if input_path is not None:
        run_suffix = _run_time_suffix(run_dir.name)
        package_name = f"{_safe_presentation_stem(input_path)}-{run_suffix}" if run_suffix else _safe_presentation_stem(input_path)
    else:
        package_name = _safe_name(run_dir.name)
    package_dir = presentation_root.expanduser().resolve() / package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    return package_dir


def write_presentation_manifest(manifest: PresentationPackageManifest) -> Path:
    manifest.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest.manifest_path


def write_presentation_batch_manifest(manifest: PresentationBatchManifest) -> Path:
    manifest.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest.manifest_path


def animation_artifact_paths(package_dir: Path) -> dict[str, Path]:
    package_dir = package_dir.expanduser().resolve()
    animation_dir = package_dir / "animation"
    return {
        "animation_dir": animation_dir,
        "frames_dir": animation_dir / "frames",
        "video_path": animation_dir / "exploded_assembly.mp4",
        "manifest_path": animation_dir / "animation_manifest.json",
        "job_path": animation_dir / "blender_job.json",
        "preview_dir": package_dir / "preview",
        "segmented_preview": package_dir / "preview" / "segmented_front.png",
        "exploded_preview": package_dir / "preview" / "exploded_view.png",
        "parts_dir": package_dir / "parts",
        "parts_manifest": package_dir / "parts" / "parts_manifest.json",
    }


def write_part_export_manifest(manifest: PartExportManifest) -> Path:
    manifest.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest.manifest_path


def write_animation_manifest(manifest: AnimationManifest) -> Path:
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


def _safe_name(value: str) -> str:
    name = value.strip().lower()
    name = re.sub(r"[^a-z0-9._-]+", "-", name)
    name = name.strip("-._")
    return name or "asset"


def _safe_presentation_stem(path: Path) -> str:
    stem = path.stem.strip()
    stem = re.sub(r"[\\/:*?\"<>|]+", "-", stem)
    stem = re.sub(r"\s+", "-", stem)
    stem = stem.strip("-._")
    return stem or "asset"


def _run_time_suffix(name: str) -> str:
    match = re.search(r"(\d{8}-\d{6})$", name)
    return match.group(1) if match else ""

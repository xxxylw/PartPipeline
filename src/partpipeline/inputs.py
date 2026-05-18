from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from partpipeline.types import InputManifest, StagedInputItem


def stage_glb_inputs(source_dir: Path, destination_dir: Path, limit: int | None = None) -> InputManifest:
    source_dir = source_dir.expanduser().resolve()
    destination_dir = destination_dir.expanduser().resolve()
    if not source_dir.exists():
        raise FileNotFoundError(f"Input source directory does not exist: {source_dir}")
    if not source_dir.is_dir():
        raise NotADirectoryError(f"Input source is not a directory: {source_dir}")

    destination_dir.mkdir(parents=True, exist_ok=True)
    glbs = sorted(path for path in source_dir.glob("*.glb") if path.is_file())
    if limit is not None:
        glbs = glbs[:limit]

    items: list[StagedInputItem] = []
    for source in glbs:
        destination = destination_dir / source.name
        shutil.copy2(source, destination)
        items.append(
            StagedInputItem(
                source_path=source.resolve(),
                staged_path=destination.resolve(),
                asset_name=source.name,
                size_bytes=destination.stat().st_size,
            )
        )

    manifest = InputManifest(
        source_dir=source_dir,
        destination_dir=destination_dir,
        created_at=datetime.now().isoformat(timespec="seconds"),
        items=items,
        manifest_path=destination_dir / "input_manifest.json",
    )
    manifest.manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest

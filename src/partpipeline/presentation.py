from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

from partpipeline.artifacts import (
    create_presentation_package_dir,
    write_presentation_batch_manifest,
    write_presentation_manifest,
)
from partpipeline.animation import render_exploded_animation
from partpipeline.types import (
    AnimationManifest,
    PresentationBatchItem,
    PresentationBatchManifest,
    PresentationLevel,
    PresentationPackageManifest,
)


class PresentationPackagingError(RuntimeError):
    pass


def package_run(
    run_dir: Path,
    presentation_dir: Path = Path("outputs/presentation"),
    include_level_b: bool = False,
    include_original: bool = False,
) -> PresentationPackageManifest:
    run_dir = run_dir.expanduser().resolve()
    source_manifest = run_dir / "manifest.json"
    if not source_manifest.exists():
        raise PresentationPackagingError(f"Run manifest does not exist: {source_manifest}")

    data = _read_json(source_manifest)
    package_dir = create_presentation_package_dir(presentation_dir, run_dir)
    input_path = _path_from_value(data.get("input_path"), base=run_dir)

    level_a_source = _level_a_source(run_dir, data)
    if not level_a_source.exists():
        raise PresentationPackagingError(f"Level A prepared GLB does not exist: {level_a_source}")
    level_a_package = package_dir / "level_a_segmented_parts.glb"
    shutil.copy2(level_a_source, level_a_package)

    levels = [
        PresentationLevel(
            level="A",
            name="segmented_parts",
            source_path=level_a_source,
            package_path=level_a_package,
            recommended_for_display=True,
            role="default_display",
            note="Recommended presentation output; preserves the segmented source geometry.",
        )
    ]

    if include_level_b:
        level_b_source = _level_b_source(run_dir, data)
        if not level_b_source.exists():
            raise PresentationPackagingError(f"Level B HoloPart output does not exist: {level_b_source}")
        level_b_package = package_dir / "level_b_holopart_output.glb"
        shutil.copy2(level_b_source, level_b_package)
        levels.append(
            PresentationLevel(
                level="B",
                name="holopart_completion",
                source_path=level_b_source,
                package_path=level_b_package,
                recommended_for_display=False,
                role="optional_comparison",
                note="Optional HoloPart comparison output; not the default display result.",
            )
        )

    part_manifest = _copy_optional_part_manifest(run_dir, data, package_dir)
    original_glb = None
    if include_original:
        if not input_path.exists():
            raise PresentationPackagingError(f"Original input GLB does not exist: {input_path}")
        original_glb = package_dir / "original.glb"
        shutil.copy2(input_path, original_glb)

    manifest = PresentationPackageManifest(
        package_dir=package_dir,
        source_run_dir=run_dir,
        source_manifest=source_manifest,
        input_path=input_path,
        default_level="A",
        levels=levels,
        part_manifest=part_manifest,
        original_glb=original_glb,
        notes=[
            "Level A is the default and recommended display artifact.",
            "Level B is copied only when explicitly requested and should be treated as optional comparison.",
            "Original GLB copying is optional; the source input path is always recorded.",
        ],
        manifest_path=package_dir / "presentation_manifest.json",
    )
    write_presentation_manifest(manifest)
    return manifest


def package_batch(
    batch_manifest_path: Path,
    presentation_dir: Path = Path("outputs/presentation"),
    include_level_b: bool = False,
    include_original: bool = False,
    generate_animation: bool = False,
    animation_options: dict[str, Any] | None = None,
    animation_func: Callable[..., AnimationManifest] | None = None,
) -> PresentationBatchManifest:
    batch_manifest_path = batch_manifest_path.expanduser().resolve()
    if not batch_manifest_path.exists():
        raise PresentationPackagingError(f"Batch manifest does not exist: {batch_manifest_path}")

    data = _read_json(batch_manifest_path)
    presentation_root = presentation_dir.expanduser().resolve()
    presentation_root.mkdir(parents=True, exist_ok=True)
    items: list[PresentationBatchItem] = []

    for index, item in enumerate(data.get("items", []), start=1):
        asset_name = str(item.get("asset_name") or f"item-{index}")
        manifest_value = item.get("manifest_path")
        if not manifest_value:
            items.append(
                PresentationBatchItem(
                    asset_name=asset_name,
                    source_manifest=None,
                    package_dir=None,
                    presentation_manifest=None,
                    status="failed",
                    error={"type": "missing_manifest_path", "message": "Batch item has no manifest_path."},
                )
            )
            continue

        source_manifest = _path_from_value(manifest_value, base=batch_manifest_path.parent)
        if not source_manifest.exists():
            items.append(
                PresentationBatchItem(
                    asset_name=asset_name,
                    source_manifest=source_manifest,
                    package_dir=None,
                    presentation_manifest=None,
                    status="failed",
                    error={
                        "type": "missing_manifest",
                        "message": f"Run manifest does not exist: {source_manifest}",
                    },
                )
            )
            continue

        try:
            package = package_run(
                source_manifest.parent,
                presentation_root,
                include_level_b=include_level_b,
                include_original=include_original,
            )
        except PresentationPackagingError as exc:
            items.append(
                PresentationBatchItem(
                    asset_name=asset_name,
                    source_manifest=source_manifest,
                    package_dir=None,
                    presentation_manifest=None,
                    status="failed",
                    error={"type": exc.__class__.__name__, "message": str(exc)},
                )
            )
            continue

        animation_manifest = None
        animation_video = None
        status = "packaged"
        if generate_animation:
            try:
                render_func = animation_func or render_exploded_animation
                animation = render_func(package.package_dir, **(animation_options or {}))
                animation_manifest = animation.manifest_path
                animation_video = animation.video_path
                status = "packaged_with_animation"
            except Exception as exc:
                items.append(
                    PresentationBatchItem(
                        asset_name=asset_name,
                        source_manifest=source_manifest,
                        package_dir=package.package_dir,
                        presentation_manifest=package.manifest_path,
                        status="failed",
                        error={"type": exc.__class__.__name__, "message": str(exc)},
                    )
                )
                continue

        items.append(
            PresentationBatchItem(
                asset_name=asset_name,
                source_manifest=source_manifest,
                package_dir=package.package_dir,
                presentation_manifest=package.manifest_path,
                status=status,
                animation_manifest=animation_manifest,
                animation_video=animation_video,
            )
        )

    manifest = PresentationBatchManifest(
        batch_manifest_path=batch_manifest_path,
        presentation_dir=presentation_root,
        items=items,
        manifest_path=presentation_root / "presentation_batch_manifest.json",
    )
    write_presentation_batch_manifest(manifest)
    return manifest


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_from_value(value: Any, base: Path) -> Path:
    if value is None:
        return base / ""
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _level_a_source(run_dir: Path, data: dict[str, Any]) -> Path:
    bridge = data.get("bridge", {})
    value = bridge.get("prepared_glb")
    if value:
        return _path_from_value(value, base=run_dir)
    return run_dir / "bridge" / "prepared_parts.glb"


def _level_b_source(run_dir: Path, data: dict[str, Any]) -> Path:
    holopart = data.get("holopart", {})
    value = holopart.get("output_glb")
    if not value:
        value = holopart.get("paths", {}).get("output_glb")
    if value:
        return _path_from_value(value, base=run_dir)
    return run_dir / "holopart" / "output.glb"


def _copy_optional_part_manifest(run_dir: Path, data: dict[str, Any], package_dir: Path) -> Path | None:
    bridge = data.get("bridge", {})
    value = bridge.get("part_manifest")
    source = _path_from_value(value, base=run_dir) if value else run_dir / "bridge" / "part_manifest.json"
    if not source.exists():
        return None
    destination = package_dir / "part_manifest.json"
    shutil.copy2(source, destination)
    return destination

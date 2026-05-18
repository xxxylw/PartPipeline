from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from dataclasses import replace

from partpipeline.artifacts import create_batch_dir, create_run_paths, write_batch_manifest, write_manifest
from partpipeline.bridge import BridgeConversionError, BridgeConverter
from partpipeline.config import load_config, resolve_profile
from partpipeline.runners.sampart3d import (
    Sampart3DExecutionError,
    Sampart3DPreflightError,
    Sampart3DRunner,
)
from partpipeline.runners.holopart import (
    HoloPartExecutionError,
    HoloPartPreflightError,
    HoloPartRunner,
)
from partpipeline.types import (
    BatchItemResult,
    BatchManifest,
    BridgeResult,
    CommandResult,
    HoloPartResult,
    RunManifest,
    RunPaths,
    RunRequest,
    RuntimeProfile,
)


class BatchExecutionError(RuntimeError):
    pass


def prepare_single_run(
    request: RunRequest,
    sampart3d_runner: Sampart3DRunner | None = None,
    bridge_converter: BridgeConverter | None = None,
) -> RunManifest:
    input_path = request.input_path.expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input GLB does not exist: {input_path}")

    config = load_config(request.config_path)
    profile = resolve_profile(config, request.profile_name)
    output_root = request.output_dir or profile.output_root
    mask_scale = request.mask_scale or config.default_mask_scale
    paths = create_run_paths(input_path, output_root)
    now = datetime.now().isoformat(timespec="seconds")
    runner = sampart3d_runner or Sampart3DRunner()
    converter = bridge_converter or BridgeConverter(config.bridge)

    if request.dry_run:
        result = runner.run(input_path, profile, paths, mask_scale, dry_run=True)
        manifest = RunManifest(
            input_path=input_path,
            profile=profile.name,
            output_root=output_root.expanduser().resolve(),
            run_dir=paths.run_dir,
            mask_scale=mask_scale,
            status="dry_run_prepared",
            created_at=now,
            updated_at=now,
            paths=paths,
            commands=[result.command],
            sampart3d=result,
        )
        write_manifest(manifest)
        return manifest

    try:
        result = runner.run(input_path, profile, paths, mask_scale, dry_run=False)
    except Sampart3DPreflightError as exc:
        manifest = _failure_manifest(
            input_path=input_path,
            profile_name=profile.name,
            output_root=output_root,
            run_dir=paths.run_dir,
            mask_scale=mask_scale,
            paths=paths,
            created_at=now,
            error_type="preflight",
            message=str(exc),
            issues=exc.issues,
        )
        write_manifest(manifest)
        raise
    except Sampart3DExecutionError as exc:
        manifest = _failure_manifest(
            input_path=input_path,
            profile_name=profile.name,
            output_root=output_root,
            run_dir=paths.run_dir,
            mask_scale=mask_scale,
            paths=paths,
            created_at=now,
            error_type="execution",
            message=str(exc),
            commands=[exc.command],
        )
        write_manifest(manifest)
        raise
    except BridgeConversionError:
        raise

    try:
        bridge_result = converter.convert(
            _source_glb_for_bridge(paths, result),
            result.copied_selected_mask or result.paths.selected_mask,
            paths,
            mask_scale,
        )
    except BridgeConversionError as exc:
        manifest = RunManifest(
            input_path=input_path,
            profile=profile.name,
            output_root=output_root.expanduser().resolve(),
            run_dir=paths.run_dir,
            mask_scale=mask_scale,
            status="failed",
            created_at=now,
            updated_at=datetime.now().isoformat(timespec="seconds"),
            paths=paths,
            commands=[result.command],
            sampart3d=result,
            error={
                "type": "bridge",
                "message": str(exc),
                "source_glb": str(_source_glb_for_bridge(paths, result)),
                "source_mask": str(result.copied_selected_mask or result.paths.selected_mask),
            },
        )
        write_manifest(manifest)
        raise

    manifest = RunManifest(
        input_path=input_path,
        profile=profile.name,
        output_root=output_root.expanduser().resolve(),
        run_dir=paths.run_dir,
        mask_scale=mask_scale,
        status="bridge_complete",
        created_at=now,
        updated_at=datetime.now().isoformat(timespec="seconds"),
        paths=paths,
        commands=[result.command],
        sampart3d=result,
        bridge=bridge_result,
    )
    write_manifest(manifest)
    return manifest


def bridge_existing_run(
    run_dir: Path,
    config_path: Path,
    profile_name: str | None = None,
    bridge_converter: BridgeConverter | None = None,
) -> RunManifest:
    run_dir = run_dir.expanduser().resolve()
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Run manifest does not exist: {manifest_path}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = load_config(config_path)
    profile = resolve_profile(config, profile_name or data.get("profile"))
    mask_scale = str(data.get("mask_scale", config.default_mask_scale))
    paths = _run_paths_from_manifest(run_dir, data)
    source_glb = _source_glb_from_manifest(paths, data)
    source_mask = _source_mask_from_manifest(paths, data, mask_scale)
    converter = bridge_converter or BridgeConverter(config.bridge)
    bridge_result = converter.convert(source_glb, source_mask, paths, mask_scale)

    updated_at = datetime.now().isoformat(timespec="seconds")
    manifest = RunManifest(
        input_path=Path(data.get("input_path", source_glb)).expanduser(),
        profile=profile.name,
        output_root=Path(data.get("output_root", paths.run_dir.parent)).expanduser().resolve(),
        run_dir=paths.run_dir,
        mask_scale=mask_scale,
        status="bridge_complete",
        created_at=str(data.get("created_at", datetime.now().isoformat(timespec="seconds"))),
        updated_at=updated_at,
        paths=paths,
        commands=[],
        bridge=bridge_result,
    )
    data.update(
        {
            "profile": profile.name,
            "output_root": str(Path(data.get("output_root", paths.run_dir.parent)).expanduser().resolve()),
            "run_dir": str(paths.run_dir),
            "mask_scale": mask_scale,
            "status": "bridge_complete",
            "updated_at": updated_at,
            "paths": paths.to_dict(),
            "bridge": bridge_result.to_dict(),
        }
    )
    data.setdefault("sampart3d", _fallback_sampart3d_record(paths, source_glb, source_mask, mask_scale))
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def run_holopart_for_existing_run(
    run_dir: Path,
    config_path: Path,
    profile_name: str | None = None,
    holopart_runner: HoloPartRunner | None = None,
    seed: int | None = None,
    num_inference_steps: int | None = None,
    guidance_scale: float | None = None,
    batch_size: int | None = None,
) -> RunManifest:
    run_dir = run_dir.expanduser().resolve()
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Run manifest does not exist: {manifest_path}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = load_config(config_path)
    profile = resolve_profile(config, profile_name or data.get("profile"))
    mask_scale = str(data.get("mask_scale", config.default_mask_scale))
    paths = _run_paths_from_manifest(run_dir, data)
    runner = holopart_runner or HoloPartRunner()

    try:
        holopart_result = runner.run(
            profile,
            paths,
            seed=seed,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            batch_size=batch_size,
        )
    except (HoloPartPreflightError, HoloPartExecutionError) as exc:
        command = getattr(exc, "command", None)
        data.update(
            {
                "status": "failed",
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "paths": paths.to_dict(),
                "error": {
                    "type": "holopart",
                    "message": str(exc),
                    "command": command.to_dict() if command is not None else None,
                },
            }
        )
        manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        raise

    updated_at = datetime.now().isoformat(timespec="seconds")
    data.update(
        {
            "profile": profile.name,
            "output_root": str(Path(data.get("output_root", paths.run_dir.parent)).expanduser().resolve()),
            "run_dir": str(paths.run_dir),
            "mask_scale": mask_scale,
            "status": "holopart_complete",
            "updated_at": updated_at,
            "paths": paths.to_dict(),
            "holopart": holopart_result.to_dict(),
        }
    )
    existing_commands = data.get("commands")
    if isinstance(existing_commands, list):
        existing_commands.append(holopart_result.command.to_dict())
    else:
        data["commands"] = [holopart_result.command.to_dict()]
    manifest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return RunManifest(
        input_path=Path(data.get("input_path", holopart_result.paths.prepared_glb)).expanduser(),
        profile=profile.name,
        output_root=Path(data.get("output_root", paths.run_dir.parent)).expanduser().resolve(),
        run_dir=paths.run_dir,
        mask_scale=mask_scale,
        status="holopart_complete",
        created_at=str(data.get("created_at", datetime.now().isoformat(timespec="seconds"))),
        updated_at=updated_at,
        paths=paths,
        commands=[holopart_result.command],
        holopart=holopart_result,
    )


def run_batch_pipeline(
    input_dir: Path,
    config_path: Path,
    profile_name: str | None = None,
    output_dir: Path | None = None,
    mask_scale: str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    continue_on_error: bool = True,
    run_holopart: bool = True,
    single_run_func=None,
    holopart_func=None,
) -> BatchManifest:
    input_dir = input_dir.expanduser().resolve()
    if not input_dir.exists():
        raise BatchExecutionError(f"Batch input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise BatchExecutionError(f"Batch input path is not a directory: {input_dir}")

    config = load_config(config_path)
    profile = resolve_profile(config, profile_name)
    output_root = (output_dir or profile.output_root).expanduser().resolve()
    resolved_mask_scale = mask_scale or config.default_mask_scale
    glbs = sorted(path for path in input_dir.glob("*.glb") if path.is_file())
    if limit is not None:
        glbs = glbs[:limit]

    created_at = datetime.now().isoformat(timespec="seconds")
    batch_dir = create_batch_dir(output_root)
    manifest = BatchManifest(
        batch_id=batch_dir.name,
        profile=profile.name,
        input_dir=input_dir,
        output_root=output_root,
        mask_scale=resolved_mask_scale,
        status="empty",
        created_at=created_at,
        updated_at=created_at,
        items=[],
        manifest_path=batch_dir / "batch_manifest.json",
    )
    write_batch_manifest(manifest)

    source_paths = _input_manifest_sources(input_dir)
    run_single = single_run_func or prepare_single_run
    run_completion = holopart_func or run_holopart_for_existing_run

    items: list[BatchItemResult] = []
    for glb in glbs:
        try:
            run_manifest = run_single(
                RunRequest(
                    input_path=glb,
                    config_path=config_path,
                    profile_name=profile.name,
                    output_dir=output_root,
                    mask_scale=resolved_mask_scale,
                    dry_run=dry_run,
                )
            )
            final_manifest = run_manifest
            if not dry_run and run_holopart:
                final_manifest = run_completion(run_manifest.run_dir, config_path, profile.name)
            item = BatchItemResult(
                asset_name=glb.name,
                input_path=glb,
                source_path=source_paths.get(glb.resolve()),
                run_dir=final_manifest.run_dir,
                manifest_path=final_manifest.paths.manifest_path,
                status=final_manifest.status,
            )
        except Exception as exc:
            item = BatchItemResult(
                asset_name=glb.name,
                input_path=glb,
                source_path=source_paths.get(glb.resolve()),
                run_dir=None,
                manifest_path=None,
                status="failed",
                error={"type": exc.__class__.__name__, "message": str(exc)},
            )
            items.append(item)
            manifest = _batch_manifest_with_items(manifest, items, dry_run)
            write_batch_manifest(manifest)
            if not continue_on_error:
                return manifest
            continue

        items.append(item)
        manifest = _batch_manifest_with_items(manifest, items, dry_run)
        write_batch_manifest(manifest)

    manifest = _batch_manifest_with_items(manifest, items, dry_run)
    write_batch_manifest(manifest)
    return manifest


def _failure_manifest(
    input_path,
    profile_name: str,
    output_root,
    run_dir,
    mask_scale: str,
    paths,
    created_at: str,
    error_type: str,
    message: str,
    issues: list[str] | None = None,
    commands: list[CommandResult] | None = None,
) -> RunManifest:
    return RunManifest(
        input_path=input_path,
        profile=profile_name,
        output_root=output_root.expanduser().resolve(),
        run_dir=run_dir,
        mask_scale=mask_scale,
        status="failed",
        created_at=created_at,
        updated_at=datetime.now().isoformat(timespec="seconds"),
        paths=paths,
        commands=commands or [],
        error={
            "type": error_type,
            "message": message,
            "issues": issues or [],
        },
    )


def _input_manifest_sources(input_dir: Path) -> dict[Path, Path]:
    manifest_path = input_dir / "input_manifest.json"
    if not manifest_path.exists():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources: dict[Path, Path] = {}
    for item in data.get("items", []):
        staged = item.get("staged_path")
        source = item.get("source_path")
        if staged and source:
            sources[Path(staged).expanduser().resolve()] = Path(source).expanduser()
    return sources


def _batch_manifest_with_items(manifest: BatchManifest, items: list[BatchItemResult], dry_run: bool) -> BatchManifest:
    return replace(
        manifest,
        items=list(items),
        status=_batch_status(items, dry_run),
        updated_at=datetime.now().isoformat(timespec="seconds"),
    )


def _batch_status(items: list[BatchItemResult], dry_run: bool) -> str:
    if not items:
        return "empty"
    if dry_run:
        return "dry_run"
    succeeded = sum(1 for item in items if item.status == "holopart_complete")
    failed = sum(1 for item in items if item.status == "failed")
    if succeeded and failed:
        return "partial"
    if failed == len(items):
        return "failed"
    return "complete"


def _source_glb_for_bridge(paths, result) -> Path:
    staged = paths.sam_dir / f"{paths.run_dir.name}.glb"
    if staged.exists():
        return staged
    return result.paths.mesh_path


def _run_paths_from_manifest(run_dir: Path, data: dict) -> RunPaths:
    paths = data.get("paths", {})
    return RunPaths(
        run_dir=Path(paths.get("run_dir", run_dir)).expanduser().resolve(),
        logs_dir=Path(paths.get("logs_dir", run_dir / "logs")).expanduser().resolve(),
        sam_dir=Path(paths.get("sam_dir", run_dir / "sam")).expanduser().resolve(),
        bridge_dir=Path(paths.get("bridge_dir", run_dir / "bridge")).expanduser().resolve(),
        prepared_dir=Path(paths.get("prepared_dir", run_dir / "prepared")).expanduser().resolve(),
        holopart_dir=Path(paths.get("holopart_dir", run_dir / "holopart")).expanduser().resolve(),
        manifest_path=Path(paths.get("manifest_path", run_dir / "manifest.json")).expanduser().resolve(),
    )


def _source_glb_from_manifest(paths: RunPaths, data: dict) -> Path:
    staged = paths.sam_dir / f"{paths.run_dir.name}.glb"
    if staged.exists():
        return staged
    sampart = data.get("sampart3d", {})
    sampart_paths = sampart.get("paths", {})
    mesh_path = sampart_paths.get("mesh_path")
    if mesh_path:
        return Path(mesh_path).expanduser().resolve()
    return Path(data["input_path"]).expanduser().resolve()


def _source_mask_from_manifest(paths: RunPaths, data: dict, mask_scale: str) -> Path:
    sampart = data.get("sampart3d", {})
    copied = sampart.get("copied_selected_mask")
    if copied:
        return Path(copied).expanduser().resolve()
    selected = sampart.get("paths", {}).get("selected_mask")
    if selected:
        return Path(selected).expanduser().resolve()
    return paths.sam_dir / f"mesh_{mask_scale}.npy"


def _fallback_sampart3d_record(paths: RunPaths, source_glb: Path, source_mask: Path, mask_scale: str) -> dict:
    exp_dir = Path("third_party/SAMPart3D/exp/sampart3d") / paths.run_dir.name
    return {
        "paths": {
            "exp_name": paths.run_dir.name,
            "mesh_path": str(source_glb),
            "render_dir": str(Path("third_party/SAMPart3D/data_root") / source_glb.stem),
            "exp_dir": str(exp_dir),
            "config_path": str(exp_dir / "config.py"),
            "results_dir": str(exp_dir / "results" / "5000"),
            "vis_dir": str(exp_dir / "vis_pcd" / "5000"),
            "selected_mask": str(source_mask),
        },
        "copied_selected_mask": str(source_mask),
        "note": "Reconstructed by bridge command from run artifacts.",
    }


def _planned_sampart3d_command(
    profile: RuntimeProfile,
    input_path,
    mask_scale: str,
) -> list[str]:
    runner = Sampart3DRunner()
    paths = runner.build_paths(profile, input_path, "{run_dir}", mask_scale)
    return runner.build_command(profile, input_path, paths.exp_name)

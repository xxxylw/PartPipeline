from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

from partpipeline.artifacts import create_run_paths, write_manifest
from partpipeline.bridge import BridgeConversionError, BridgeConverter
from partpipeline.config import load_config, resolve_profile
from partpipeline.runners.sampart3d import (
    Sampart3DExecutionError,
    Sampart3DPreflightError,
    Sampart3DRunner,
)
from partpipeline.types import BridgeResult, CommandResult, RunManifest, RunPaths, RunRequest, RuntimeProfile


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

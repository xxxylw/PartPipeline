from __future__ import annotations

from datetime import datetime

from partpipeline.artifacts import create_run_paths, write_manifest
from partpipeline.config import load_config, resolve_profile
from partpipeline.runners.sampart3d import (
    Sampart3DExecutionError,
    Sampart3DPreflightError,
    Sampart3DRunner,
)
from partpipeline.types import CommandResult, RunManifest, RunRequest, RuntimeProfile


def prepare_single_run(
    request: RunRequest,
    sampart3d_runner: Sampart3DRunner | None = None,
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

    manifest = RunManifest(
        input_path=input_path,
        profile=profile.name,
        output_root=output_root.expanduser().resolve(),
        run_dir=paths.run_dir,
        mask_scale=mask_scale,
        status="sampart3d_complete",
        created_at=now,
        updated_at=datetime.now().isoformat(timespec="seconds"),
        paths=paths,
        commands=[result.command],
        sampart3d=result,
    )
    write_manifest(manifest)
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


def _planned_sampart3d_command(
    profile: RuntimeProfile,
    input_path,
    mask_scale: str,
) -> list[str]:
    runner = Sampart3DRunner()
    paths = runner.build_paths(profile, input_path, "{run_dir}", mask_scale)
    return runner.build_command(profile, input_path, paths.exp_name)

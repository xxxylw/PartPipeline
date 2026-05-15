from __future__ import annotations

from datetime import datetime

from partpipeline.artifacts import create_run_paths, write_manifest
from partpipeline.config import load_config, resolve_profile
from partpipeline.types import CommandResult, RunManifest, RunRequest, RuntimeProfile


def prepare_single_run(request: RunRequest) -> RunManifest:
    input_path = request.input_path.expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input GLB does not exist: {input_path}")

    config = load_config(request.config_path)
    profile = resolve_profile(config, request.profile_name)
    output_root = request.output_dir or profile.output_root
    mask_scale = request.mask_scale or config.default_mask_scale
    paths = create_run_paths(input_path, output_root)
    now = datetime.now().isoformat(timespec="seconds")
    command = _planned_sampart3d_command(profile, input_path, mask_scale)

    manifest = RunManifest(
        input_path=input_path,
        profile=profile.name,
        output_root=output_root.expanduser().resolve(),
        run_dir=paths.run_dir,
        mask_scale=mask_scale,
        status="dry_run_prepared" if request.dry_run else "prepared",
        created_at=now,
        updated_at=now,
        paths=paths,
        commands=[
            CommandResult(
                command=command,
                cwd=profile.sampart3d.repo,
                exit_code=None,
                stdout_log=paths.logs_dir / "sampart3d.stdout.log",
                stderr_log=paths.logs_dir / "sampart3d.stderr.log",
                dry_run=True,
                env={
                    "CONDA_DEFAULT_ENV": profile.sampart3d.env or "",
                    "PARTPIPELINE_PROFILE": profile.name,
                },
            )
        ],
    )
    write_manifest(manifest)
    return manifest


def _planned_sampart3d_command(
    profile: RuntimeProfile,
    input_path,
    mask_scale: str,
) -> list[str]:
    return [
        str(profile.sampart3d.python),
        "-m",
        "SAMPart3D.placeholder",
        "--input",
        str(input_path),
        "--output-dir",
        "{run_dir}/sam",
        "--mask-scale",
        mask_scale,
    ]

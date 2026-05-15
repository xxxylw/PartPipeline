from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from partpipeline.config import load_config, resolve_profile
from partpipeline.orchestrator import prepare_single_run
from partpipeline.types import RunRequest


app = typer.Typer(help="PartPipeline runtime for GLB part segmentation workflows.")


@app.command()
def run(
    input_glb: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o"),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
    mask_scale: Optional[str] = typer.Option(None, "--mask-scale"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Prepare a single GLB pipeline run and write a manifest."""
    manifest = prepare_single_run(
        RunRequest(
            input_path=input_glb,
            config_path=config,
            profile_name=profile,
            output_dir=output_dir,
            mask_scale=mask_scale,
            dry_run=dry_run,
        )
    )
    typer.echo(f"Profile: {manifest.profile}")
    typer.echo(f"Status: {manifest.status}")
    typer.echo(f"Run directory: {manifest.run_dir}")
    typer.echo(f"Manifest: {manifest.paths.manifest_path}")


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o"),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Inspect a directory of GLBs using the selected runtime profile."""
    runtime_config = load_config(config)
    runtime_profile = resolve_profile(runtime_config, profile)
    glbs = sorted(input_dir.glob("*.glb"))
    destination = output_dir or runtime_profile.output_root

    typer.echo(f"Profile: {runtime_profile.name}")
    typer.echo(f"GLB count: {len(glbs)}")
    typer.echo(f"Output root: {destination}")
    typer.echo(f"Dry run: {dry_run}")


if __name__ == "__main__":
    app()

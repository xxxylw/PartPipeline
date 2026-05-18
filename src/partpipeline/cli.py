from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from partpipeline.config import load_config, resolve_profile
from partpipeline.bridge import BridgeConversionError
from partpipeline.inputs import stage_glb_inputs
from partpipeline.orchestrator import (
    BatchExecutionError,
    bridge_existing_run,
    prepare_single_run,
    run_batch_pipeline,
    run_holopart_for_existing_run,
)
from partpipeline.runners.holopart import HoloPartExecutionError, HoloPartPreflightError
from partpipeline.runners.sampart3d import Sampart3DExecutionError, Sampart3DPreflightError
from partpipeline.types import RunRequest


app = typer.Typer(help="PartPipeline runtime for GLB part segmentation workflows.")


@app.command("stage-inputs")
def stage_inputs(
    source_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    destination: Path = typer.Option(Path("inputs/phase7"), "--destination"),
    limit: Optional[int] = typer.Option(None, "--limit"),
) -> None:
    """Copy GLB inputs into a PartPipeline-managed input directory."""
    manifest = stage_glb_inputs(source_dir, destination, limit)
    typer.echo(f"Source: {manifest.source_dir}")
    typer.echo(f"Destination: {manifest.destination_dir}")
    typer.echo(f"GLB count: {len(manifest.items)}")
    typer.echo(f"Input manifest: {manifest.manifest_path}")


@app.command()
def run(
    input_glb: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o"),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
    mask_scale: Optional[str] = typer.Option(None, "--mask-scale"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Run or prepare a single GLB pipeline run and write a manifest."""
    try:
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
    except (Sampart3DPreflightError, Sampart3DExecutionError, BridgeConversionError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Profile: {manifest.profile}")
    typer.echo(f"Status: {manifest.status}")
    typer.echo(f"Run directory: {manifest.run_dir}")
    typer.echo(f"Manifest: {manifest.paths.manifest_path}")


@app.command()
def bridge(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
) -> None:
    """Convert an existing SAMPart3D run into HoloPart multipart GLB input."""
    try:
        manifest = bridge_existing_run(run_dir, config, profile)
    except (BridgeConversionError, FileNotFoundError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Profile: {manifest.profile}")
    typer.echo(f"Status: {manifest.status}")
    if manifest.bridge is not None:
        typer.echo(f"Prepared GLB: {manifest.bridge.prepared_glb}")
        typer.echo(f"Part manifest: {manifest.bridge.part_manifest}")
    typer.echo(f"Manifest: {manifest.paths.manifest_path}")


@app.command()
def holopart(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
    seed: Optional[int] = typer.Option(None, "--seed"),
    num_inference_steps: Optional[int] = typer.Option(None, "--num-inference-steps"),
    guidance_scale: Optional[float] = typer.Option(None, "--guidance-scale"),
    batch_size: Optional[int] = typer.Option(None, "--batch-size"),
) -> None:
    """Run HoloPart for an existing bridge-complete run."""
    try:
        manifest = run_holopart_for_existing_run(
            run_dir,
            config,
            profile,
            seed=seed,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            batch_size=batch_size,
        )
    except (HoloPartPreflightError, HoloPartExecutionError, FileNotFoundError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Profile: {manifest.profile}")
    typer.echo(f"Status: {manifest.status}")
    if manifest.holopart is not None:
        typer.echo(f"Output GLB: {manifest.holopart.output_glb}")
    typer.echo(f"Manifest: {manifest.paths.manifest_path}")


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o"),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p"),
    mask_scale: Optional[str] = typer.Option(None, "--mask-scale"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    limit: Optional[int] = typer.Option(None, "--limit"),
    stop_on_error: bool = typer.Option(False, "--stop-on-error"),
    skip_holopart: bool = typer.Option(False, "--skip-holopart"),
) -> None:
    """Run a directory of GLBs through the PartPipeline workflow."""
    try:
        manifest = run_batch_pipeline(
            input_dir,
            config,
            profile,
            output_dir=output_dir,
            mask_scale=mask_scale,
            dry_run=dry_run,
            limit=limit,
            continue_on_error=not stop_on_error,
            run_holopart=not skip_holopart,
        )
    except BatchExecutionError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Profile: {manifest.profile}")
    typer.echo(f"Status: {manifest.status}")
    typer.echo(f"Total: {manifest.total}")
    typer.echo(f"Succeeded: {manifest.succeeded}")
    typer.echo(f"Failed: {manifest.failed}")
    typer.echo(f"Batch manifest: {manifest.manifest_path}")


if __name__ == "__main__":
    app()

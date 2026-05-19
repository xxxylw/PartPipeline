from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from partpipeline.animation import AnimationGenerationError, render_exploded_animation
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
from partpipeline.presentation import PresentationPackagingError, package_batch, package_run
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


@app.command("package")
def package(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    presentation_dir: Path = typer.Option(Path("outputs/presentation"), "--presentation-dir"),
    include_level_b: bool = typer.Option(False, "--include-level-b"),
    include_original: bool = typer.Option(False, "--include-original"),
) -> None:
    """Package a completed run into presentation-ready Level A/Level B outputs."""
    try:
        manifest = package_run(
            run_dir,
            presentation_dir,
            include_level_b=include_level_b,
            include_original=include_original,
        )
    except PresentationPackagingError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Package directory: {manifest.package_dir}")
    typer.echo(f"Manifest: {manifest.manifest_path}")
    typer.echo(f"Default level: {manifest.default_level}")


@app.command("package-batch")
def package_batch_command(
    batch_manifest: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
    presentation_dir: Path = typer.Option(Path("outputs/presentation"), "--presentation-dir"),
    include_level_b: bool = typer.Option(False, "--include-level-b"),
    include_original: bool = typer.Option(False, "--include-original"),
    generate_animation: bool = typer.Option(False, "--generate-animation"),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    blender_path: Optional[Path] = typer.Option(None, "--blender-path"),
    ffmpeg_path: Optional[Path] = typer.Option(None, "--ffmpeg-path"),
    duration_seconds: Optional[float] = typer.Option(None, "--duration-seconds"),
    fps: Optional[int] = typer.Option(None, "--fps"),
    width: Optional[int] = typer.Option(None, "--width"),
    height: Optional[int] = typer.Option(None, "--height"),
    explode_scale: Optional[float] = typer.Option(None, "--explode-scale"),
    rotation_degrees: Optional[float] = typer.Option(None, "--rotation-degrees"),
) -> None:
    """Package all usable runs from a batch manifest into presentation-ready outputs."""
    try:
        manifest = package_batch(
            batch_manifest,
            presentation_dir,
            include_level_b=include_level_b,
            include_original=include_original,
            generate_animation=generate_animation,
            animation_options=_animation_options_from_cli(
                config=config,
                blender_path=blender_path,
                ffmpeg_path=ffmpeg_path,
                duration_seconds=duration_seconds,
                fps=fps,
                width=width,
                height=height,
                explode_scale=explode_scale,
                rotation_degrees=rotation_degrees,
            )
            if generate_animation
            else None,
        )
    except (PresentationPackagingError, AnimationGenerationError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Presentation directory: {manifest.presentation_dir}")
    typer.echo(f"Batch presentation manifest: {manifest.manifest_path}")
    typer.echo(f"Total: {manifest.total}")
    typer.echo(f"Packaged: {manifest.packaged}")
    typer.echo(f"Failed: {manifest.failed}")


@app.command("animate")
def animate(
    package_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    config: Path = typer.Option(Path("configs/default.yaml"), "--config", "-c"),
    blender_path: Optional[Path] = typer.Option(None, "--blender-path"),
    ffmpeg_path: Optional[Path] = typer.Option(None, "--ffmpeg-path"),
    duration_seconds: Optional[float] = typer.Option(None, "--duration-seconds"),
    fps: Optional[int] = typer.Option(None, "--fps"),
    width: Optional[int] = typer.Option(None, "--width"),
    height: Optional[int] = typer.Option(None, "--height"),
    explode_scale: Optional[float] = typer.Option(None, "--explode-scale"),
    rotation_degrees: Optional[float] = typer.Option(None, "--rotation-degrees"),
) -> None:
    """Export per-part GLBs and render an exploded assembly MP4 for a Level A package."""
    try:
        manifest = render_exploded_animation(
            package_dir,
            **_animation_options_from_cli(
                config=config,
                blender_path=blender_path,
                ffmpeg_path=ffmpeg_path,
                duration_seconds=duration_seconds,
                fps=fps,
                width=width,
                height=height,
                explode_scale=explode_scale,
                rotation_degrees=rotation_degrees,
            ),
        )
    except AnimationGenerationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Package directory: {manifest.package_dir}")
    typer.echo(f"Animation directory: {manifest.animation_dir}")
    typer.echo(f"Parts manifest: {manifest.part_manifest}")
    typer.echo(f"Video: {manifest.video_path}")
    typer.echo(f"Animation manifest: {manifest.manifest_path}")
    typer.echo(f"Frame count: {manifest.frame_count}")
    typer.echo(f"Part count: {_part_count_from_manifest(manifest.part_manifest)}")


def _animation_options_from_cli(
    *,
    config: Path,
    blender_path: Optional[Path],
    ffmpeg_path: Optional[Path],
    duration_seconds: Optional[float],
    fps: Optional[int],
    width: Optional[int],
    height: Optional[int],
    explode_scale: Optional[float] = None,
    rotation_degrees: Optional[float] = None,
) -> dict[str, object]:
    config_data = load_config(config)
    animation = config_data.raw.get("pipeline", {}).get("animation", {})
    options: dict[str, object] = {
        "blender_path": Path(animation.get("blender", "blender")),
        "ffmpeg_path": Path(animation.get("ffmpeg", "ffmpeg")),
        "duration_seconds": float(animation.get("default_duration_seconds", 4.0)),
        "fps": int(animation.get("fps", 24)),
        "width": int(animation.get("width", 1280)),
        "height": int(animation.get("height", 720)),
        "explode_scale": float(animation.get("explode_scale", 1.25)),
        "rotation_degrees": float(animation.get("rotation_degrees", 15.0)),
    }
    if blender_path is not None:
        options["blender_path"] = blender_path
    if ffmpeg_path is not None:
        options["ffmpeg_path"] = ffmpeg_path
    if duration_seconds is not None:
        options["duration_seconds"] = duration_seconds
    if fps is not None:
        options["fps"] = fps
    if width is not None:
        options["width"] = width
    if height is not None:
        options["height"] = height
    if explode_scale is not None:
        options["explode_scale"] = explode_scale
    if rotation_degrees is not None:
        options["rotation_degrees"] = rotation_degrees
    return options


def _part_count_from_manifest(path: Path) -> int:
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    return int(data.get("total", 0))


if __name__ == "__main__":
    app()

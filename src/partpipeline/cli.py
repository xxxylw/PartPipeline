from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Run the PartPipeline GLB segmentation and completion workflow.")


@app.command()
def run(
    glb: Path = typer.Argument(..., exists=True, dir_okay=False, help="Input .glb file."),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Run output directory."),
    mask_scale: str = typer.Option("1.0", "--mask-scale", help="SAMPart3D mesh mask scale to use."),
) -> None:
    """Prepare a single-object pipeline run."""
    target = output_dir or Path("outputs") / glb.stem
    typer.echo("PartPipeline run scaffold")
    typer.echo(f"input: {glb}")
    typer.echo(f"output_dir: {target}")
    typer.echo(f"mask_scale: {mask_scale}")
    typer.echo("Model execution is planned for later phases.")


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, help="Directory containing .glb files."),
    output_dir: Path = typer.Option(Path("outputs"), "--output-dir", "-o", help="Batch output root."),
    mask_scale: str = typer.Option("1.0", "--mask-scale", help="SAMPart3D mesh mask scale to use."),
) -> None:
    """Prepare a batch pipeline run."""
    glbs = sorted(input_dir.glob("*.glb"))
    typer.echo("PartPipeline batch scaffold")
    typer.echo(f"input_dir: {input_dir}")
    typer.echo(f"output_dir: {output_dir}")
    typer.echo(f"mask_scale: {mask_scale}")
    typer.echo(f"found_glb_count: {len(glbs)}")
    typer.echo("Model execution is planned for later phases.")


if __name__ == "__main__":
    app()

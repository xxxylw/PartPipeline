from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Sequence

import trimesh

from partpipeline.artifacts import (
    animation_artifact_paths,
    write_animation_manifest,
    write_part_export_manifest,
)
from partpipeline.types import (
    AnimationManifest,
    AnimationToolStatus,
    PartExportItem,
    PartExportManifest,
)


class AnimationGenerationError(RuntimeError):
    pass


Runner = Callable[..., subprocess.CompletedProcess[str]]


def export_parts(package_dir: Path) -> PartExportManifest:
    package_dir = package_dir.expanduser().resolve()
    source_level_a = resolve_level_a_path(package_dir)
    paths = animation_artifact_paths(package_dir)
    parts_dir = paths["parts_dir"]
    parts_dir.mkdir(parents=True, exist_ok=True)

    scene_or_mesh = trimesh.load(source_level_a, force="scene")
    parts = _extract_mesh_parts(scene_or_mesh)
    if not parts:
        raise AnimationGenerationError(f"No mesh parts found in Level A GLB: {source_level_a}")

    items: list[PartExportItem] = []
    for index, (source_name, mesh) in enumerate(parts, start=1):
        part_name = f"part_{index:03d}"
        part_path = parts_dir / f"{part_name}.glb"
        mesh.export(part_path)
        items.append(
            PartExportItem(
                index=index,
                name=part_name,
                source_geometry=source_name,
                path=part_path,
                centroid=[float(value) for value in mesh.centroid],
                bounds=[[float(value) for value in row] for row in mesh.bounds],
                vertex_count=int(len(mesh.vertices)) if hasattr(mesh, "vertices") else None,
                face_count=int(len(mesh.faces)) if hasattr(mesh, "faces") else None,
            )
        )

    manifest = PartExportManifest(
        package_dir=package_dir,
        source_level_a=source_level_a,
        parts_dir=parts_dir,
        items=items,
        manifest_path=paths["parts_manifest"],
    )
    write_part_export_manifest(manifest)
    return manifest


def render_exploded_animation(
    package_dir: Path,
    *,
    blender_path: Path | None = None,
    ffmpeg_path: Path | None = None,
    duration_seconds: float = 5.0,
    fps: int = 24,
    width: int = 1280,
    height: int = 720,
    explode_scale: float = 1.25,
    rotation_degrees: float = 15.0,
    view: str = "three_quarter",
    runner: Runner | None = None,
) -> AnimationManifest:
    package_dir = package_dir.expanduser().resolve()
    if duration_seconds <= 0:
        raise AnimationGenerationError("duration_seconds must be greater than 0.")
    if fps <= 0:
        raise AnimationGenerationError("fps must be greater than 0.")

    part_manifest = export_parts(package_dir)
    paths = animation_artifact_paths(package_dir)
    animation_dir = paths["animation_dir"]
    frames_dir = paths["frames_dir"]
    animation_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    tools = preflight_animation_tools(blender_path=blender_path, ffmpeg_path=ffmpeg_path, runner=runner)
    frame_count = max(2, int(math.ceil(duration_seconds * fps)))
    job = {
        "package_dir": str(package_dir),
        "source_level_a": str(part_manifest.source_level_a),
        "parts_manifest": str(part_manifest.manifest_path),
        "frames_dir": str(frames_dir),
        "preview_dir": str(paths["preview_dir"]),
        "frame_pattern": "frame_####.png",
        "frame_count": frame_count,
        "fps": fps,
        "width": width,
        "height": height,
        "explode_scale": explode_scale,
        "rotation_degrees": rotation_degrees,
        "view": view,
    }
    paths["job_path"].write_text(json.dumps(job, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    script_path = Path(__file__).resolve().parents[2] / "scripts" / "render_exploded_assembly.py"
    blender_command = [
        str(tools.blender_path),
        "--background",
        "--python",
        str(script_path),
        "--",
        str(paths["job_path"]),
    ]
    ffmpeg_command = [
        str(tools.ffmpeg_path),
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%04d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(paths["video_path"]),
    ]

    command_runner = runner or subprocess.run
    _run_command(command_runner, blender_command, cwd=package_dir)
    _run_command(command_runner, ffmpeg_command, cwd=package_dir)
    if not paths["video_path"].exists():
        raise AnimationGenerationError(f"ffmpeg did not produce video: {paths['video_path']}")

    manifest = AnimationManifest(
        package_dir=package_dir,
        source_level_a=part_manifest.source_level_a,
        animation_dir=animation_dir,
        frames_dir=frames_dir,
        video_path=paths["video_path"],
        part_manifest=part_manifest.manifest_path,
        duration_seconds=duration_seconds,
        fps=fps,
        frame_count=frame_count,
        width=width,
        height=height,
        explode_scale=explode_scale,
        rotation_degrees=rotation_degrees,
        view=view,
        tools=tools,
        commands=[blender_command, ffmpeg_command],
        manifest_path=paths["manifest_path"],
        preview_images={
            "segmented_front": paths["segmented_preview"],
            "exploded_view": paths["exploded_preview"],
        },
    )
    write_animation_manifest(manifest)
    return manifest


def preflight_animation_tools(
    *,
    blender_path: Path | None = None,
    ffmpeg_path: Path | None = None,
    runner: Runner | None = None,
) -> AnimationToolStatus:
    blender = _resolve_executable(blender_path, "blender")
    ffmpeg = _resolve_executable(ffmpeg_path, "ffmpeg")
    command_runner = runner or subprocess.run
    return AnimationToolStatus(
        blender_path=blender,
        ffmpeg_path=ffmpeg,
        blender_version=_tool_version(command_runner, [str(blender), "--version"]),
        ffmpeg_version=_tool_version(command_runner, [str(ffmpeg), "-version"]),
    )


def resolve_level_a_path(package_dir: Path) -> Path:
    package_dir = package_dir.expanduser().resolve()
    manifest_path = package_dir / "presentation_manifest.json"
    if manifest_path.exists():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for level in data.get("levels", []):
            if level.get("level") == "A":
                value = level.get("package_path")
                if value:
                    path = _path_from_value(value, package_dir)
                    if path.exists():
                        return path
    fallback = package_dir / "level_a_segmented_parts.glb"
    if fallback.exists():
        return fallback.resolve()
    raise AnimationGenerationError(f"Level A GLB does not exist in package: {package_dir}")


def _extract_mesh_parts(scene_or_mesh: Any) -> list[tuple[str, trimesh.Trimesh]]:
    if isinstance(scene_or_mesh, trimesh.Trimesh):
        return [("mesh", scene_or_mesh)]

    if not isinstance(scene_or_mesh, trimesh.Scene):
        return []

    dumped = scene_or_mesh.dump(concatenate=False)
    meshes = [mesh for mesh in dumped if isinstance(mesh, trimesh.Trimesh)] if isinstance(dumped, list) else []
    names = sorted(scene_or_mesh.geometry.keys())
    if len(meshes) == len(names):
        return [(names[index], mesh) for index, mesh in enumerate(meshes)]

    parts: list[tuple[str, trimesh.Trimesh]] = []
    for name in names:
        geometry = scene_or_mesh.geometry[name]
        if isinstance(geometry, trimesh.Trimesh):
            parts.append((name, geometry.copy()))
    return parts


def _resolve_executable(path: Path | None, executable: str) -> Path:
    if path is not None:
        resolved = path.expanduser().resolve()
        if resolved.exists():
            return resolved
        raise AnimationGenerationError(f"{executable} executable does not exist: {resolved}")

    found = shutil.which(executable)
    if found:
        return Path(found).resolve()
    raise AnimationGenerationError(
        f"{executable} executable was not found. Install it in the part environment or pass --{executable}-path."
    )


def _tool_version(runner: Runner, command: Sequence[str]) -> str | None:
    try:
        result = runner(command, capture_output=True, text=True, check=False)
    except OSError:
        return None
    output = (result.stdout or result.stderr or "").splitlines()
    return output[0] if output else None


def _run_command(runner: Runner, command: Sequence[str], cwd: Path) -> None:
    try:
        result = runner(command, cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise AnimationGenerationError(f"Failed to run command: {' '.join(command)}") from exc
    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise AnimationGenerationError(f"Command failed ({result.returncode}): {' '.join(command)}\n{stderr}")


def _path_from_value(value: Any, base: Path) -> Path:
    path = Path(str(value)).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()

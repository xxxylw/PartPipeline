from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ServerSSH:
    host_alias: str
    hostname: str
    user: str
    port: int


@dataclass(frozen=True)
class ToolRuntime:
    name: str
    repo: Path
    python: Path
    env: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BridgeConfig:
    merge_small_parts: bool = True
    min_faces_per_part: int = 100
    min_area_ratio: float = 0.001
    validate_holopart_prepare_data: bool = False


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    project_root: Path
    output_root: Path
    sampart3d: ToolRuntime
    holopart: ToolRuntime
    server_ssh: ServerSSH | None = None
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineConfig:
    path: Path
    active_profile: str
    profiles: dict[str, RuntimeProfile]
    default_mask_scale: str
    environment_strategy: str
    bridge: BridgeConfig = field(default_factory=BridgeConfig)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunRequest:
    input_path: Path
    config_path: Path
    profile_name: str | None = None
    output_dir: Path | None = None
    mask_scale: str | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class StagedInputItem:
    source_path: Path
    staged_path: Path
    asset_name: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "staged_path": str(self.staged_path),
            "asset_name": self.asset_name,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class InputManifest:
    source_dir: Path
    destination_dir: Path
    created_at: str
    items: list[StagedInputItem]
    manifest_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_dir": str(self.source_dir),
            "destination_dir": str(self.destination_dir),
            "created_at": self.created_at,
            "items": [item.to_dict() for item in self.items],
            "manifest_path": str(self.manifest_path),
        }


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    logs_dir: Path
    sam_dir: Path
    bridge_dir: Path
    prepared_dir: Path
    holopart_dir: Path
    manifest_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "run_dir": str(self.run_dir),
            "logs_dir": str(self.logs_dir),
            "sam_dir": str(self.sam_dir),
            "bridge_dir": str(self.bridge_dir),
            "prepared_dir": str(self.prepared_dir),
            "holopart_dir": str(self.holopart_dir),
            "manifest_path": str(self.manifest_path),
        }


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    cwd: Path
    exit_code: int | None
    stdout_log: Path
    stderr_log: Path
    dry_run: bool = False
    env: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "cwd": str(self.cwd),
            "exit_code": self.exit_code,
            "stdout_log": str(self.stdout_log),
            "stderr_log": str(self.stderr_log),
            "dry_run": self.dry_run,
            "env": self.env,
        }


@dataclass(frozen=True)
class Sampart3DPaths:
    exp_name: str
    mesh_path: Path
    render_dir: Path
    exp_dir: Path
    config_path: Path
    results_dir: Path
    vis_dir: Path
    selected_mask: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "exp_name": self.exp_name,
            "mesh_path": str(self.mesh_path),
            "render_dir": str(self.render_dir),
            "exp_dir": str(self.exp_dir),
            "config_path": str(self.config_path),
            "results_dir": str(self.results_dir),
            "vis_dir": str(self.vis_dir),
            "selected_mask": str(self.selected_mask),
        }


@dataclass(frozen=True)
class Sampart3DResult:
    paths: Sampart3DPaths
    command: CommandResult
    copied_selected_mask: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "paths": self.paths.to_dict(),
            "command": self.command.to_dict(),
            "copied_selected_mask": str(self.copied_selected_mask)
            if self.copied_selected_mask is not None
            else None,
        }


@dataclass(frozen=True)
class BridgePartStats:
    label: int
    name: str
    face_count: int
    face_ratio: float
    area: float
    merged_from: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "name": self.name,
            "face_count": self.face_count,
            "face_ratio": self.face_ratio,
            "area": self.area,
            "merged_from": self.merged_from,
        }


@dataclass(frozen=True)
class BridgeMergeRecord:
    source_label: int
    target_label: int
    method: str
    reason: str
    face_count: int
    boundary_count: int | None = None
    distance: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_label": self.source_label,
            "target_label": self.target_label,
            "method": self.method,
            "reason": self.reason,
            "face_count": self.face_count,
        }
        if self.boundary_count is not None:
            data["boundary_count"] = self.boundary_count
        if self.distance is not None:
            data["distance"] = self.distance
        return data


@dataclass(frozen=True)
class BridgeResult:
    source_glb: Path
    source_mask: Path
    prepared_glb: Path
    merged_mask: Path
    part_manifest: Path
    original_part_count: int
    final_part_count: int
    parts: list[BridgePartStats]
    merge_history: list[BridgeMergeRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_glb": str(self.source_glb),
            "source_mask": str(self.source_mask),
            "prepared_glb": str(self.prepared_glb),
            "merged_mask": str(self.merged_mask),
            "part_manifest": str(self.part_manifest),
            "original_part_count": self.original_part_count,
            "final_part_count": self.final_part_count,
            "parts": [part.to_dict() for part in self.parts],
            "merge_history": [record.to_dict() for record in self.merge_history],
        }


@dataclass(frozen=True)
class HoloPartPaths:
    prepared_glb: Path
    output_dir: Path
    output_glb: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "prepared_glb": str(self.prepared_glb),
            "output_dir": str(self.output_dir),
            "output_glb": str(self.output_glb),
        }


@dataclass(frozen=True)
class HoloPartResult:
    paths: HoloPartPaths
    command: CommandResult

    @property
    def output_glb(self) -> Path:
        return self.paths.output_glb

    def to_dict(self) -> dict[str, Any]:
        return {
            "paths": self.paths.to_dict(),
            "output_glb": str(self.paths.output_glb),
            "command": self.command.to_dict(),
        }


@dataclass(frozen=True)
class BatchItemResult:
    asset_name: str
    input_path: Path
    source_path: Path | None
    run_dir: Path | None
    manifest_path: Path | None
    status: str
    error: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_name": self.asset_name,
            "input_path": str(self.input_path),
            "source_path": str(self.source_path) if self.source_path is not None else None,
            "run_dir": str(self.run_dir) if self.run_dir is not None else None,
            "manifest_path": str(self.manifest_path) if self.manifest_path is not None else None,
            "status": self.status,
            "error": self.error,
        }


@dataclass(frozen=True)
class BatchManifest:
    batch_id: str
    profile: str
    input_dir: Path
    output_root: Path
    mask_scale: str
    status: str
    created_at: str
    updated_at: str
    items: list[BatchItemResult]
    manifest_path: Path

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def succeeded(self) -> int:
        return sum(1 for item in self.items if item.status == "holopart_complete")

    @property
    def failed(self) -> int:
        return sum(1 for item in self.items if item.status == "failed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "profile": self.profile,
            "input_dir": str(self.input_dir),
            "output_root": str(self.output_root),
            "mask_scale": self.mask_scale,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "items": [item.to_dict() for item in self.items],
            "manifest_path": str(self.manifest_path),
        }


@dataclass(frozen=True)
class RunManifest:
    input_path: Path
    profile: str
    output_root: Path
    run_dir: Path
    mask_scale: str
    status: str
    created_at: str
    updated_at: str
    paths: RunPaths
    commands: list[CommandResult] = field(default_factory=list)
    sampart3d: Sampart3DResult | None = None
    bridge: BridgeResult | None = None
    holopart: HoloPartResult | None = None
    error: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "input_path": str(self.input_path),
            "profile": self.profile,
            "output_root": str(self.output_root),
            "run_dir": str(self.run_dir),
            "mask_scale": self.mask_scale,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "paths": self.paths.to_dict(),
            "commands": [command.to_dict() for command in self.commands],
        }
        if self.sampart3d is not None:
            data["sampart3d"] = self.sampart3d.to_dict()
        if self.bridge is not None:
            data["bridge"] = self.bridge.to_dict()
        if self.holopart is not None:
            data["holopart"] = self.holopart.to_dict()
        if self.error is not None:
            data["error"] = self.error
        return data


@dataclass(frozen=True)
class PresentationLevel:
    level: str
    name: str
    source_path: Path
    package_path: Path
    recommended_for_display: bool
    role: str
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "level": self.level,
            "name": self.name,
            "source_path": str(self.source_path),
            "package_path": str(self.package_path),
            "recommended_for_display": self.recommended_for_display,
            "role": self.role,
        }
        if self.note is not None:
            data["note"] = self.note
        return data


@dataclass(frozen=True)
class PresentationPackageManifest:
    package_dir: Path
    source_run_dir: Path
    source_manifest: Path
    input_path: Path
    default_level: str
    levels: list[PresentationLevel]
    part_manifest: Path | None
    original_glb: Path | None
    notes: list[str]
    manifest_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_dir": str(self.package_dir),
            "source_run_dir": str(self.source_run_dir),
            "source_manifest": str(self.source_manifest),
            "input_path": str(self.input_path),
            "default_level": self.default_level,
            "levels": [level.to_dict() for level in self.levels],
            "part_manifest": str(self.part_manifest) if self.part_manifest is not None else None,
            "original_glb": str(self.original_glb) if self.original_glb is not None else None,
            "notes": self.notes,
            "manifest_path": str(self.manifest_path),
        }


@dataclass(frozen=True)
class PartExportItem:
    index: int
    name: str
    source_geometry: str
    path: Path
    centroid: list[float]
    bounds: list[list[float]]
    vertex_count: int | None = None
    face_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "source_geometry": self.source_geometry,
            "path": str(self.path),
            "centroid": self.centroid,
            "bounds": self.bounds,
            "vertex_count": self.vertex_count,
            "face_count": self.face_count,
        }


@dataclass(frozen=True)
class PartExportManifest:
    package_dir: Path
    source_level_a: Path
    parts_dir: Path
    items: list[PartExportItem]
    manifest_path: Path

    @property
    def total(self) -> int:
        return len(self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_dir": str(self.package_dir),
            "source_level_a": str(self.source_level_a),
            "parts_dir": str(self.parts_dir),
            "total": self.total,
            "items": [item.to_dict() for item in self.items],
            "manifest_path": str(self.manifest_path),
        }


@dataclass(frozen=True)
class AnimationToolStatus:
    blender_path: Path
    ffmpeg_path: Path
    blender_version: str | None = None
    ffmpeg_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "blender_path": str(self.blender_path),
            "ffmpeg_path": str(self.ffmpeg_path),
            "blender_version": self.blender_version,
            "ffmpeg_version": self.ffmpeg_version,
        }


@dataclass(frozen=True)
class AnimationManifest:
    package_dir: Path
    source_level_a: Path
    animation_dir: Path
    frames_dir: Path
    video_path: Path
    part_manifest: Path
    duration_seconds: float
    fps: int
    frame_count: int
    width: int
    height: int
    explode_scale: float
    rotation_degrees: float
    view: str
    tools: AnimationToolStatus
    commands: list[list[str]]
    manifest_path: Path
    preview_images: dict[str, Path] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_dir": str(self.package_dir),
            "source_level_a": str(self.source_level_a),
            "animation_dir": str(self.animation_dir),
            "frames_dir": str(self.frames_dir),
            "video_path": str(self.video_path),
            "part_manifest": str(self.part_manifest),
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "width": self.width,
            "height": self.height,
            "explode_scale": self.explode_scale,
            "rotation_degrees": self.rotation_degrees,
            "view": self.view,
            "tools": self.tools.to_dict(),
            "commands": self.commands,
            "manifest_path": str(self.manifest_path),
            "preview_images": {name: str(path) for name, path in self.preview_images.items()},
        }


@dataclass(frozen=True)
class PresentationBatchItem:
    asset_name: str
    source_manifest: Path | None
    package_dir: Path | None
    presentation_manifest: Path | None
    status: str
    error: dict[str, str] | None = None
    animation_manifest: Path | None = None
    animation_video: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_name": self.asset_name,
            "source_manifest": str(self.source_manifest) if self.source_manifest is not None else None,
            "package_dir": str(self.package_dir) if self.package_dir is not None else None,
            "presentation_manifest": str(self.presentation_manifest)
            if self.presentation_manifest is not None
            else None,
            "status": self.status,
            "error": self.error,
            "animation_manifest": str(self.animation_manifest) if self.animation_manifest is not None else None,
            "animation_video": str(self.animation_video) if self.animation_video is not None else None,
        }


@dataclass(frozen=True)
class PresentationBatchManifest:
    batch_manifest_path: Path
    presentation_dir: Path
    items: list[PresentationBatchItem]
    manifest_path: Path

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def packaged(self) -> int:
        return sum(1 for item in self.items if item.status in {"packaged", "packaged_with_animation"})

    @property
    def failed(self) -> int:
        return sum(1 for item in self.items if item.status == "failed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_manifest_path": str(self.batch_manifest_path),
            "presentation_dir": str(self.presentation_dir),
            "total": self.total,
            "packaged": self.packaged,
            "failed": self.failed,
            "items": [item.to_dict() for item in self.items],
            "manifest_path": str(self.manifest_path),
        }

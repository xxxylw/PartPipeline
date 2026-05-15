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

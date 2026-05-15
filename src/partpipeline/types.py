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
    prepared_dir: Path
    holopart_dir: Path
    manifest_path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "run_dir": str(self.run_dir),
            "logs_dir": str(self.logs_dir),
            "sam_dir": str(self.sam_dir),
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

    def to_dict(self) -> dict[str, Any]:
        return {
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

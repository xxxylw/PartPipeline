from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from partpipeline.types import PipelineConfig, RuntimeProfile, ServerSSH, ToolRuntime


class ConfigError(ValueError):
    """Raised when a runtime config is missing or malformed."""


def load_config(path: Path) -> PipelineConfig:
    config_path = path.expanduser().resolve()
    if not config_path.exists():
        raise ConfigError(f"Config file does not exist: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a YAML mapping: {config_path}")

    active_profile = _required_str(data, "active_profile")
    environment = _required_mapping(data, "environment")
    pipeline = _required_mapping(data, "pipeline")
    profiles_data = _required_mapping(data, "profiles")
    project_root = _default_project_root(config_path)

    profiles: dict[str, RuntimeProfile] = {}
    for name, profile_data in profiles_data.items():
        if not isinstance(name, str) or not isinstance(profile_data, dict):
            raise ConfigError("Each profile must be a named mapping")
        profiles[name] = _load_profile(name, profile_data, project_root)

    if active_profile not in profiles:
        raise ConfigError(f"Active profile {active_profile!r} is not defined")

    return PipelineConfig(
        path=config_path,
        active_profile=active_profile,
        profiles=profiles,
        default_mask_scale=str(pipeline.get("default_mask_scale", "1.0")),
        environment_strategy=str(environment.get("strategy", "dispatcher")),
        raw=data,
    )


def resolve_profile(config: PipelineConfig, profile_name: str | None) -> RuntimeProfile:
    name = profile_name or config.active_profile
    try:
        return config.profiles[name]
    except KeyError as exc:
        available = ", ".join(sorted(config.profiles))
        raise ConfigError(f"Unknown profile {name!r}; available profiles: {available}") from exc


def _load_profile(
    name: str,
    data: dict[str, Any],
    default_project_root: Path,
) -> RuntimeProfile:
    project_root = _resolve_path(data.get("project_root", default_project_root), default_project_root)
    output_root = _resolve_path(_required_str(data, "output_root"), default_project_root)
    sampart3d = _load_tool_runtime("sampart3d", _required_mapping(data, "sampart3d"), project_root)
    holopart = _load_tool_runtime("holopart", _required_mapping(data, "holopart"), project_root)
    ssh_data = data.get("ssh")

    server_ssh = None
    if ssh_data is not None:
        if not isinstance(ssh_data, dict):
            raise ConfigError(f"profile {name!r} ssh must be a mapping")
        server_ssh = ServerSSH(
            host_alias=_required_str(ssh_data, "host_alias"),
            hostname=_required_str(ssh_data, "hostname"),
            user=_required_str(ssh_data, "user"),
            port=int(ssh_data.get("port", 22)),
        )

    return RuntimeProfile(
        name=name,
        project_root=project_root,
        output_root=output_root,
        sampart3d=sampart3d,
        holopart=holopart,
        server_ssh=server_ssh,
        settings={key: value for key, value in data.items() if key not in _PROFILE_KEYS},
    )


def _load_tool_runtime(name: str, data: dict[str, Any], project_root: Path) -> ToolRuntime:
    return ToolRuntime(
        name=name,
        repo=_resolve_path(_required_str(data, "repo"), project_root),
        python=_resolve_path(_required_str(data, "python"), project_root),
        env=str(data["env"]) if data.get("env") is not None else None,
        settings={key: value for key, value in data.items() if key not in {"repo", "python", "env"}},
    )


def _default_project_root(config_path: Path) -> Path:
    if config_path.parent.name == "configs":
        return config_path.parent.parent
    return config_path.parent


def _resolve_path(value: str | Path, base: Path) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate
    return (base / candidate).resolve()


def _required_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"Missing required mapping: {key}")
    return value


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None or not isinstance(value, (str, int, float)):
        raise ConfigError(f"Missing required value: {key}")
    return str(value)


_PROFILE_KEYS = {
    "project_root",
    "output_root",
    "sampart3d",
    "holopart",
    "ssh",
}

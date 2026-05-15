from __future__ import annotations

import os
from pathlib import Path

from partpipeline.artifacts import copy_selected_mask
from partpipeline.runners.base import SubprocessRunner
from partpipeline.types import CommandResult, RunPaths, RuntimeProfile, Sampart3DPaths, Sampart3DResult


class Sampart3DPreflightError(RuntimeError):
    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__("SAMPart3D preflight failed: " + "; ".join(issues))


class Sampart3DExecutionError(RuntimeError):
    def __init__(self, message: str, command: CommandResult) -> None:
        self.command = command
        super().__init__(message)


class Sampart3DRunner:
    def __init__(self, subprocess_runner: SubprocessRunner | None = None) -> None:
        self.subprocess_runner = subprocess_runner or SubprocessRunner()

    def run(
        self,
        input_path: Path,
        profile: RuntimeProfile,
        run_paths: RunPaths,
        mask_scale: str,
        dry_run: bool = False,
        weight_name: str = "5000",
    ) -> Sampart3DResult:
        input_path = input_path.expanduser().resolve()
        paths = self.build_paths(profile, input_path, run_paths.run_dir.name, mask_scale, weight_name)
        command = self.build_command(profile, input_path, paths.exp_name, weight_name)
        env = {
            "CONDA_DEFAULT_ENV": profile.sampart3d.env or "",
            "PARTPIPELINE_PROFILE": profile.name,
            "PYTHONPATH": str(profile.sampart3d.repo),
        }

        if not dry_run:
            self.preflight(profile, input_path, paths)
            _, cuda_env = self.prepare_cuda_loader(profile)
            env.update(cuda_env)

        command_result = self.subprocess_runner.run(
            command,
            cwd=profile.sampart3d.repo,
            logs_dir=run_paths.logs_dir,
            name="sampart3d",
            env=env,
            dry_run=dry_run,
        )

        copied_mask = None
        if not dry_run:
            if command_result.exit_code != 0:
                raise Sampart3DExecutionError(
                    f"SAMPart3D exited with code {command_result.exit_code}",
                    command_result,
                )
            copied_mask = copy_selected_mask(paths.selected_mask, run_paths.sam_dir)

        return Sampart3DResult(paths=paths, command=command_result, copied_selected_mask=copied_mask)

    def build_paths(
        self,
        profile: RuntimeProfile,
        input_path: Path,
        exp_name: str,
        mask_scale: str,
        weight_name: str = "5000",
    ) -> Sampart3DPaths:
        repo = profile.sampart3d.repo
        object_name = input_path.stem
        exp_dir = repo / "exp" / "sampart3d" / exp_name
        results_dir = exp_dir / "results" / weight_name
        return Sampart3DPaths(
            exp_name=exp_name,
            mesh_path=repo / "mesh_root" / f"{object_name}.glb",
            render_dir=repo / "data_root" / object_name,
            exp_dir=exp_dir,
            config_path=exp_dir / "config.py",
            results_dir=results_dir,
            vis_dir=exp_dir / "vis_pcd" / weight_name,
            selected_mask=results_dir / f"mesh_{mask_scale}.npy",
        )

    def build_command(
        self,
        profile: RuntimeProfile,
        input_path: Path,
        exp_name: str,
        weight_name: str = "5000",
    ) -> list[str]:
        repo = profile.sampart3d.repo
        return [
            str(profile.sampart3d.python),
            str(repo / "tools" / "run_sampart3d_object.py"),
            "--glb",
            str(input_path),
            "--exp-name",
            exp_name,
            "--weight-name",
            weight_name,
            "--blender",
            str(self.blender_path(profile)),
            "--backbone-weight",
            str(self.backbone_weight_path(profile)),
            "--config-template",
            str(self.config_template_path(profile)),
        ]

    def preflight(self, profile: RuntimeProfile, input_path: Path, paths: Sampart3DPaths) -> None:
        issues = []
        checks = [
            ("input GLB", input_path),
            ("SAMPart3D repo", profile.sampart3d.repo),
            ("SAMPart3D python", profile.sampart3d.python),
            ("SAMPart3D wrapper", profile.sampart3d.repo / "tools" / "run_sampart3d_object.py"),
            ("SAMPart3D config template", self.config_template_path(profile)),
            ("Blender executable", self.blender_path(profile)),
            ("SAMPart3D backbone weight", self.backbone_weight_path(profile)),
        ]
        for label, path in checks:
            if not path.exists():
                issues.append(f"{label} missing: {path}")

        try:
            self._torch_lib_dir(profile)
            self._find_torch_library(profile, "libcudart")
            self._find_torch_library(profile, "libnvrtc")
        except FileNotFoundError as exc:
            issues.append(str(exc))

        if issues:
            raise Sampart3DPreflightError(issues)

    def prepare_cuda_loader(self, profile: RuntimeProfile) -> tuple[Path, dict[str, str]]:
        cuda_dir = profile.project_root / "outputs" / "run_state" / "part_cuda_lib"
        cuda_dir.mkdir(parents=True, exist_ok=True)
        torch_lib = self._torch_lib_dir(profile)
        self._symlink_library(self._find_torch_library(profile, "libcudart"), cuda_dir / "libcudart.so")
        self._symlink_library(self._find_torch_library(profile, "libnvrtc"), cuda_dir / "libnvrtc.so")
        ld_parts = [str(cuda_dir), str(torch_lib)]
        existing = os.environ.get("LD_LIBRARY_PATH")
        if existing:
            ld_parts.append(existing)
        return cuda_dir, {"LD_LIBRARY_PATH": ":".join(ld_parts)}

    def blender_path(self, profile: RuntimeProfile) -> Path:
        configured = profile.sampart3d.settings.get("blender")
        if configured:
            return Path(configured).expanduser()
        return profile.sampart3d.repo / "blender-4.0.0-linux-x64" / "blender"

    def backbone_weight_path(self, profile: RuntimeProfile) -> Path:
        configured = profile.sampart3d.settings.get("backbone_weight")
        if configured:
            return Path(configured).expanduser()
        return profile.sampart3d.repo / "ckpt" / "ptv3-object.pth"

    def config_template_path(self, profile: RuntimeProfile) -> Path:
        configured = profile.sampart3d.settings.get("config_template")
        if configured:
            return Path(configured).expanduser()
        return profile.sampart3d.repo / "configs" / "sampart3d" / "sampart3d-trainmlp-render16views.py"

    def _torch_lib_dir(self, profile: RuntimeProfile) -> Path:
        env_root = profile.sampart3d.python.parent.parent
        candidates = sorted((env_root / "lib").glob("python*/site-packages/torch/lib"))
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"torch lib directory missing under: {env_root / 'lib'}")

    def _find_torch_library(self, profile: RuntimeProfile, prefix: str) -> Path:
        torch_lib = self._torch_lib_dir(profile)
        candidates = sorted(torch_lib.glob(f"{prefix}*.so*"))
        candidates = [candidate for candidate in candidates if candidate.name != f"{prefix}.so"]
        if not candidates:
            raise FileNotFoundError(f"{prefix} source library missing in: {torch_lib}")
        return candidates[0]

    def _symlink_library(self, source: Path, link: Path) -> None:
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(source)

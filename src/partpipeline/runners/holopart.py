from __future__ import annotations

from pathlib import Path

from partpipeline.runners.base import SubprocessRunner
from partpipeline.types import CommandResult, HoloPartPaths, HoloPartResult, RunPaths, RuntimeProfile


class HoloPartPreflightError(RuntimeError):
    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__("HoloPart preflight failed: " + "; ".join(issues))


class HoloPartExecutionError(RuntimeError):
    def __init__(self, message: str, command: CommandResult) -> None:
        self.command = command
        super().__init__(message)


class HoloPartRunner:
    def __init__(self, subprocess_runner: SubprocessRunner | None = None) -> None:
        self.subprocess_runner = subprocess_runner or SubprocessRunner()

    def run(
        self,
        profile: RuntimeProfile,
        run_paths: RunPaths,
        dry_run: bool = False,
        seed: int | None = None,
        num_inference_steps: int | None = None,
        guidance_scale: float | None = None,
        batch_size: int | None = None,
    ) -> HoloPartResult:
        paths = self.build_paths(run_paths)
        command = self.build_command(
            profile,
            paths,
            seed=seed,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            batch_size=batch_size,
        )
        env = self.build_env(profile)

        if not dry_run:
            self.preflight(profile, paths)

        command_result = self.subprocess_runner.run(
            command,
            cwd=profile.holopart.repo,
            logs_dir=run_paths.logs_dir,
            name="holopart",
            env=env,
            dry_run=dry_run,
        )

        if not dry_run:
            if command_result.exit_code != 0:
                raise HoloPartExecutionError(
                    f"HoloPart exited with code {command_result.exit_code}",
                    command_result,
                )
            if not paths.output_glb.exists():
                raise HoloPartExecutionError(
                    f"HoloPart completed but output.glb is missing: {paths.output_glb}",
                    command_result,
                )

        return HoloPartResult(paths=paths, command=command_result)

    def build_paths(self, run_paths: RunPaths) -> HoloPartPaths:
        return HoloPartPaths(
            prepared_glb=run_paths.bridge_dir / "prepared_parts.glb",
            output_dir=run_paths.holopart_dir,
            output_glb=run_paths.holopart_dir / "output.glb",
        )

    def build_command(
        self,
        profile: RuntimeProfile,
        paths: HoloPartPaths,
        seed: int | None = None,
        num_inference_steps: int | None = None,
        guidance_scale: float | None = None,
        batch_size: int | None = None,
    ) -> list[str]:
        settings = profile.holopart.settings
        return [
            str(profile.holopart.python),
            str(profile.holopart.repo / "scripts" / "inference_holopart.py"),
            "--mesh-input",
            str(paths.prepared_glb),
            "--output-dir",
            str(paths.output_dir),
            "--seed",
            str(seed if seed is not None else settings.get("seed", 42)),
            "--num-inference-steps",
            str(num_inference_steps if num_inference_steps is not None else settings.get("num_inference_steps", 50)),
            "--guidance-scale",
            str(guidance_scale if guidance_scale is not None else settings.get("guidance_scale", 3.5)),
            "--batch_size",
            str(batch_size if batch_size is not None else settings.get("batch_size", 8)),
        ]

    def build_env(self, profile: RuntimeProfile) -> dict[str, str]:
        return {
            "CONDA_DEFAULT_ENV": profile.holopart.env or "",
            "PARTPIPELINE_PROFILE": profile.name,
            "PYTHONPATH": str(profile.holopart.repo),
            "HF_ENDPOINT": str(profile.holopart.settings.get("hf_endpoint", "https://hf-mirror.com")),
        }

    def preflight(self, profile: RuntimeProfile, paths: HoloPartPaths) -> None:
        checks = [
            ("prepared HoloPart input", paths.prepared_glb),
            ("HoloPart repo", profile.holopart.repo),
            ("HoloPart python", profile.holopart.python),
            ("HoloPart inference script", profile.holopart.repo / "scripts" / "inference_holopart.py"),
        ]
        issues = [f"{label} missing: {path}" for label, path in checks if not path.exists()]
        if issues:
            raise HoloPartPreflightError(issues)
        paths.output_dir.mkdir(parents=True, exist_ok=True)

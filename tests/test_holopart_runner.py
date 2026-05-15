from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.artifacts import create_run_paths
from partpipeline.runners.holopart import HoloPartExecutionError, HoloPartPreflightError, HoloPartRunner
from partpipeline.types import CommandResult, RuntimeProfile, ServerSSH, ToolRuntime


class FakeSubprocessRunner:
    def __init__(self, exit_code: int = 0, write_output: bool = True) -> None:
        self.exit_code = exit_code
        self.write_output = write_output
        self.calls: list[dict[str, object]] = []

    def run(self, command, cwd, logs_dir, name, env=None, dry_run=False):
        self.calls.append({"command": command, "cwd": cwd, "env": env or {}, "dry_run": dry_run})
        logs_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = logs_dir / f"{name}.stdout.log"
        stderr_log = logs_dir / f"{name}.stderr.log"
        stdout_log.write_text("stdout", encoding="utf-8")
        stderr_log.write_text("stderr", encoding="utf-8")
        if self.write_output and not dry_run:
            out_dir = Path(command[command.index("--output-dir") + 1])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "output.glb").write_bytes(b"glb")
        return CommandResult(
            command=command,
            cwd=cwd,
            exit_code=None if dry_run else self.exit_code,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
            dry_run=dry_run,
            env=env or {},
        )


def make_profile(root: Path) -> RuntimeProfile:
    repo = root / "HoloPart"
    python = root / "envs" / "holopart" / "bin" / "python"
    return RuntimeProfile(
        name="local_wsl",
        project_root=root / "PartPipeline",
        output_root=root / "PartPipeline" / "outputs" / "runs",
        sampart3d=ToolRuntime(name="sampart3d", repo=root / "SAMPart3D", python=root / "part" / "bin" / "python"),
        holopart=ToolRuntime(
            name="holopart",
            repo=repo,
            python=python,
            env="holopart",
            settings={
                "hf_endpoint": "https://hf-mirror.com",
                "seed": 42,
                "num_inference_steps": 50,
                "guidance_scale": 3.5,
                "batch_size": 8,
            },
        ),
        server_ssh=ServerSSH("d5", "10.1.6.8", "qzqd5", 19091),
    )


def create_fake_holopart_layout(root: Path) -> RuntimeProfile:
    profile = make_profile(root)
    (profile.holopart.repo / "scripts").mkdir(parents=True)
    (profile.holopart.repo / "scripts" / "inference_holopart.py").write_text("# script", encoding="utf-8")
    profile.holopart.python.parent.mkdir(parents=True)
    profile.holopart.python.write_text("python", encoding="utf-8")
    return profile


class HoloPartRunnerTests(unittest.TestCase):
    def test_dry_run_builds_command_and_sets_hf_mirror(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = create_fake_holopart_layout(root)
            prepared = root / "input.glb"
            prepared.write_bytes(b"glb")
            paths = create_run_paths(prepared, root / "runs", timestamp="20260515-120000")
            prepared.rename(paths.bridge_dir / "prepared_parts.glb")
            fake = FakeSubprocessRunner()

            result = HoloPartRunner(fake).run(profile, paths, dry_run=True)

            command = result.command.command
            self.assertIn("inference_holopart.py", command[1])
            self.assertEqual(command[command.index("--mesh-input") + 1], str(paths.bridge_dir / "prepared_parts.glb"))
            self.assertEqual(command[command.index("--output-dir") + 1], str(paths.holopart_dir))
            self.assertEqual(command[command.index("--batch_size") + 1], "8")
            self.assertEqual(result.command.env["HF_ENDPOINT"], "https://hf-mirror.com")
            self.assertEqual(result.command.env["CONDA_DEFAULT_ENV"], "holopart")

    def test_preflight_reports_missing_prepared_glb(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = create_fake_holopart_layout(root)
            paths = create_run_paths(root / "input.glb", root / "runs", timestamp="20260515-120000")

            with self.assertRaisesRegex(HoloPartPreflightError, "prepared_parts.glb"):
                HoloPartRunner(FakeSubprocessRunner()).run(profile, paths)

    def test_success_requires_output_glb(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = create_fake_holopart_layout(root)
            paths = create_run_paths(root / "input.glb", root / "runs", timestamp="20260515-120000")
            (paths.bridge_dir / "prepared_parts.glb").write_bytes(b"glb")

            result = HoloPartRunner(FakeSubprocessRunner()).run(profile, paths)

            self.assertEqual(result.output_glb, paths.holopart_dir / "output.glb")
            self.assertTrue(result.output_glb.exists())

    def test_zero_exit_missing_output_is_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = create_fake_holopart_layout(root)
            paths = create_run_paths(root / "input.glb", root / "runs", timestamp="20260515-120000")
            (paths.bridge_dir / "prepared_parts.glb").write_bytes(b"glb")

            with self.assertRaisesRegex(HoloPartExecutionError, "output.glb"):
                HoloPartRunner(FakeSubprocessRunner(write_output=False)).run(profile, paths)


if __name__ == "__main__":
    unittest.main()

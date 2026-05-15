from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.artifacts import create_run_paths
from partpipeline.runners.sampart3d import Sampart3DPreflightError, Sampart3DRunner
from partpipeline.types import CommandResult, RuntimeProfile, ServerSSH, ToolRuntime


class FakeSubprocessRunner:
    def __init__(self, selected_mask: Path | None = None, exit_code: int = 0) -> None:
        self.selected_mask = selected_mask
        self.exit_code = exit_code
        self.calls: list[dict[str, object]] = []

    def run(
        self,
        command: list[str],
        cwd: Path,
        logs_dir: Path,
        name: str,
        env: dict[str, str] | None = None,
        dry_run: bool = False,
    ) -> CommandResult:
        self.calls.append({"command": command, "cwd": cwd, "env": env or {}, "dry_run": dry_run})
        logs_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = logs_dir / f"{name}.stdout.log"
        stderr_log = logs_dir / f"{name}.stderr.log"
        stdout_log.write_text("fake stdout", encoding="utf-8")
        stderr_log.write_text("", encoding="utf-8")
        if self.selected_mask is not None:
            self.selected_mask.parent.mkdir(parents=True, exist_ok=True)
            self.selected_mask.write_bytes(b"mask")
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
    repo = root / "SAMPart3D"
    python = root / "env" / "bin" / "python"
    return RuntimeProfile(
        name="local_wsl",
        project_root=root / "PartPipeline",
        output_root=root / "PartPipeline" / "outputs" / "runs",
        sampart3d=ToolRuntime(name="sampart3d", repo=repo, python=python, env="part"),
        holopart=ToolRuntime(
            name="holopart",
            repo=root / "HoloPart",
            python=root / "envs" / "holopart" / "bin" / "python",
            env="holopart",
        ),
        server_ssh=ServerSSH("d5", "10.1.6.8", "qzqd5", 19091),
    )


def create_fake_sampart3d_layout(root: Path) -> RuntimeProfile:
    profile = make_profile(root)
    repo = profile.sampart3d.repo
    (repo / "tools").mkdir(parents=True)
    (repo / "tools" / "run_sampart3d_object.py").write_text("# wrapper", encoding="utf-8")
    (repo / "configs" / "sampart3d").mkdir(parents=True)
    (repo / "configs" / "sampart3d" / "sampart3d-trainmlp-render16views.py").write_text(
        "# config",
        encoding="utf-8",
    )
    (repo / "blender-4.0.0-linux-x64").mkdir()
    (repo / "blender-4.0.0-linux-x64" / "blender").write_text("blender", encoding="utf-8")
    (repo / "ckpt").mkdir()
    (repo / "ckpt" / "ptv3-object.pth").write_bytes(b"weight")
    profile.sampart3d.python.parent.mkdir(parents=True)
    profile.sampart3d.python.write_text("python", encoding="utf-8")
    torch_lib = (
        profile.sampart3d.python.parent.parent
        / "lib"
        / "python3.10"
        / "site-packages"
        / "torch"
        / "lib"
    )
    torch_lib.mkdir(parents=True)
    (torch_lib / "libcudart-abc.so.12").write_text("cuda", encoding="utf-8")
    (torch_lib / "libnvrtc-def.so.12").write_text("nvrtc", encoding="utf-8")
    return profile


class Sampart3DRunnerTests(unittest.TestCase):
    def test_dry_run_builds_command_and_records_part_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = make_profile(root)
            glb = root / "input.glb"
            glb.write_text("glb", encoding="utf-8")
            paths = create_run_paths(glb, root / "runs", timestamp="20260515-120000")
            fake = FakeSubprocessRunner()

            result = Sampart3DRunner(fake).run(
                input_path=glb,
                profile=profile,
                run_paths=paths,
                mask_scale="1.0",
                dry_run=True,
            )

            self.assertEqual(fake.calls[0]["dry_run"], True)
            self.assertIn("run_sampart3d_object.py", " ".join(result.command.command))
            self.assertIn("--weight-name", result.command.command)
            self.assertIn("5000", result.command.command)
            self.assertEqual(result.command.env["CONDA_DEFAULT_ENV"], "part")
            self.assertEqual(result.paths.selected_mask.name, "mesh_1.0.npy")

    def test_real_run_stages_input_to_space_free_glb_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = create_fake_sampart3d_layout(root)
            glb = root / "08.Toulouse 双人沙发组合.glb"
            glb.write_text("glb", encoding="utf-8")
            paths = create_run_paths(glb, root / "runs", timestamp="20260515-120000")
            expected_mask = (
                profile.sampart3d.repo
                / "exp"
                / "sampart3d"
                / paths.run_dir.name
                / "results"
                / "5000"
                / "mesh_1.0.npy"
            )
            fake = FakeSubprocessRunner(selected_mask=expected_mask)

            Sampart3DRunner(fake).run(
                input_path=glb,
                profile=profile,
                run_paths=paths,
                mask_scale="1.0",
                dry_run=False,
            )

            command = fake.calls[0]["command"]
            glb_arg = command[command.index("--glb") + 1]
            self.assertEqual(Path(glb_arg).name, f"{paths.run_dir.name}.glb")
            self.assertNotIn(" ", Path(glb_arg).stem)
            self.assertTrue(Path(glb_arg).exists())

    def test_cuda_loader_symlinks_are_created_from_torch_libs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = create_fake_sampart3d_layout(root)
            cuda_dir, env = Sampart3DRunner().prepare_cuda_loader(profile)

            self.assertTrue((cuda_dir / "libcudart.so").is_symlink())
            self.assertTrue((cuda_dir / "libnvrtc.so").is_symlink())
            self.assertIn(str(cuda_dir), env["LD_LIBRARY_PATH"])
            self.assertIn("torch/lib", env["LD_LIBRARY_PATH"])

    def test_preflight_reports_missing_backbone_weight_before_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = create_fake_sampart3d_layout(root)
            (profile.sampart3d.repo / "ckpt" / "ptv3-object.pth").unlink()
            glb = root / "input.glb"
            glb.write_text("glb", encoding="utf-8")
            paths = create_run_paths(glb, root / "runs", timestamp="20260515-120000")
            fake = FakeSubprocessRunner()

            with self.assertRaisesRegex(Sampart3DPreflightError, "ptv3-object.pth"):
                Sampart3DRunner(fake).run(
                    input_path=glb,
                    profile=profile,
                    run_paths=paths,
                    mask_scale="1.0",
                    dry_run=False,
                )

            self.assertEqual(fake.calls, [])

    def test_success_copies_selected_mask_into_run_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile = create_fake_sampart3d_layout(root)
            glb = root / "input.glb"
            glb.write_text("glb", encoding="utf-8")
            paths = create_run_paths(glb, root / "runs", timestamp="20260515-120000")
            expected_mask = (
                profile.sampart3d.repo
                / "exp"
                / "sampart3d"
                / paths.run_dir.name
                / "results"
                / "5000"
                / "mesh_1.0.npy"
            )
            fake = FakeSubprocessRunner(selected_mask=expected_mask)

            result = Sampart3DRunner(fake).run(
                input_path=glb,
                profile=profile,
                run_paths=paths,
                mask_scale="1.0",
                dry_run=False,
            )

            self.assertEqual(result.command.exit_code, 0)
            self.assertEqual(result.copied_selected_mask, paths.sam_dir / "mesh_1.0.npy")
            self.assertEqual(result.copied_selected_mask.read_bytes(), b"mask")


if __name__ == "__main__":
    unittest.main()

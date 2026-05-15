from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.orchestrator import prepare_single_run, run_holopart_for_existing_run
from partpipeline.types import (
    BridgeResult,
    CommandResult,
    HoloPartPaths,
    HoloPartResult,
    RunRequest,
    Sampart3DPaths,
    Sampart3DResult,
)


class OrchestratorTests(unittest.TestCase):
    def test_prepare_single_run_creates_manifest_without_models(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            glb = temp_root / "demo sofa.glb"
            glb.write_text("placeholder", encoding="utf-8")

            manifest = prepare_single_run(
                RunRequest(
                    input_path=glb,
                    config_path=ROOT / "configs" / "default.yaml",
                    profile_name="server",
                    output_dir=temp_root / "runs",
                    mask_scale=None,
                    dry_run=True,
                )
            )

            saved = json.loads(manifest.paths.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["profile"], "server")
            self.assertEqual(saved["status"], "dry_run_prepared")
            self.assertEqual(saved["mask_scale"], "1.0")
            self.assertTrue(manifest.paths.logs_dir.is_dir())
            self.assertEqual(saved["commands"][0]["dry_run"], True)
            self.assertIn("SAMPart3D", " ".join(saved["commands"][0]["command"]))

    def test_prepare_single_run_records_sampart3d_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            glb = temp_root / "demo.glb"
            glb.write_text("placeholder", encoding="utf-8")

            class FakeRunner:
                def run(self, input_path, profile, run_paths, mask_scale, dry_run=False):
                    selected = run_paths.sam_dir / f"mesh_{mask_scale}.npy"
                    selected.write_bytes(b"mask")
                    return Sampart3DResult(
                        paths=Sampart3DPaths(
                            exp_name=run_paths.run_dir.name,
                            mesh_path=profile.sampart3d.repo / "mesh_root" / input_path.name,
                            render_dir=profile.sampart3d.repo / "data_root" / input_path.stem,
                            exp_dir=profile.sampart3d.repo / "exp" / "sampart3d" / run_paths.run_dir.name,
                            config_path=profile.sampart3d.repo / "exp" / "sampart3d" / run_paths.run_dir.name / "config.py",
                            results_dir=profile.sampart3d.repo / "exp" / "sampart3d" / run_paths.run_dir.name / "results" / "5000",
                            vis_dir=profile.sampart3d.repo / "exp" / "sampart3d" / run_paths.run_dir.name / "vis_pcd" / "5000",
                            selected_mask=selected,
                        ),
                        command=CommandResult(
                            command=["fake"],
                            cwd=profile.sampart3d.repo,
                            exit_code=0,
                            stdout_log=run_paths.logs_dir / "sampart3d.stdout.log",
                            stderr_log=run_paths.logs_dir / "sampart3d.stderr.log",
                        ),
                        copied_selected_mask=selected,
                    )

            class FakeBridgeConverter:
                def convert(self, glb_path, mask_path, run_paths, mask_scale):
                    prepared = run_paths.bridge_dir / "prepared_parts.glb"
                    merged = run_paths.bridge_dir / f"mesh_{mask_scale}_merged.npy"
                    part_manifest = run_paths.bridge_dir / "part_manifest.json"
                    prepared.write_bytes(b"glb")
                    merged.write_bytes(b"mask")
                    part_manifest.write_text("{}", encoding="utf-8")
                    return BridgeResult(
                        source_glb=glb_path,
                        source_mask=mask_path,
                        prepared_glb=prepared,
                        merged_mask=merged,
                        part_manifest=part_manifest,
                        original_part_count=2,
                        final_part_count=2,
                        parts=[],
                        merge_history=[],
                    )

            manifest = prepare_single_run(
                RunRequest(
                    input_path=glb,
                    config_path=ROOT / "configs" / "default.yaml",
                    output_dir=temp_root / "runs",
                    dry_run=False,
                ),
                sampart3d_runner=FakeRunner(),
                bridge_converter=FakeBridgeConverter(),
            )

            saved = json.loads(manifest.paths.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "bridge_complete")
            self.assertEqual(saved["sampart3d"]["copied_selected_mask"], str(manifest.paths.sam_dir / "mesh_1.0.npy"))
            self.assertEqual(saved["bridge"]["prepared_glb"], str(manifest.paths.bridge_dir / "prepared_parts.glb"))
            self.assertEqual(saved["commands"][0]["exit_code"], 0)

    def test_run_holopart_for_existing_run_preserves_manifest_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "demo-20260515-120000"
            bridge_dir = run_dir / "bridge"
            holopart_dir = run_dir / "holopart"
            logs_dir = run_dir / "logs"
            for directory in (bridge_dir, holopart_dir, logs_dir):
                directory.mkdir(parents=True)
            prepared = bridge_dir / "prepared_parts.glb"
            prepared.write_bytes(b"glb")
            manifest_data = {
                "input_path": str(prepared),
                "profile": "local_wsl",
                "output_root": str(root),
                "run_dir": str(run_dir),
                "mask_scale": "1.0",
                "status": "bridge_complete",
                "created_at": "2026-05-15T12:00:00",
                "updated_at": "2026-05-15T12:00:00",
                "paths": {
                    "run_dir": str(run_dir),
                    "logs_dir": str(logs_dir),
                    "sam_dir": str(run_dir / "sam"),
                    "bridge_dir": str(bridge_dir),
                    "prepared_dir": str(run_dir / "prepared"),
                    "holopart_dir": str(holopart_dir),
                    "manifest_path": str(run_dir / "manifest.json"),
                },
                "commands": [{"command": ["old"]}],
                "sampart3d": {"kept": True},
                "bridge": {"prepared_glb": str(prepared)},
            }
            (run_dir / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

            class FakeHoloPartRunner:
                def run(self, profile, run_paths, **kwargs):
                    output = run_paths.holopart_dir / "output.glb"
                    output.write_bytes(b"out")
                    return HoloPartResult(
                        paths=HoloPartPaths(
                            prepared_glb=run_paths.bridge_dir / "prepared_parts.glb",
                            output_dir=run_paths.holopart_dir,
                            output_glb=output,
                        ),
                        command=CommandResult(
                            command=["holopart"],
                            cwd=profile.holopart.repo,
                            exit_code=0,
                            stdout_log=run_paths.logs_dir / "holopart.stdout.log",
                            stderr_log=run_paths.logs_dir / "holopart.stderr.log",
                        ),
                    )

            manifest = run_holopart_for_existing_run(
                run_dir,
                ROOT / "configs" / "default.yaml",
                holopart_runner=FakeHoloPartRunner(),
            )

            saved = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest.status, "holopart_complete")
            self.assertEqual(saved["status"], "holopart_complete")
            self.assertIn("sampart3d", saved)
            self.assertIn("bridge", saved)
            self.assertIn("holopart", saved)
            self.assertEqual(saved["holopart"]["output_glb"], str(holopart_dir / "output.glb"))


if __name__ == "__main__":
    unittest.main()

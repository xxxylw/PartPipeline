from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.orchestrator import prepare_single_run
from partpipeline.types import BridgeResult, CommandResult, RunRequest, Sampart3DPaths, Sampart3DResult


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


if __name__ == "__main__":
    unittest.main()

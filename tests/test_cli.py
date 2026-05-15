from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import trimesh
from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.cli import app


class CliTests(unittest.TestCase):
    def test_run_command_writes_manifest_and_applies_mask_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            glb = temp_root / "demo.glb"
            output_root = temp_root / "runs"
            glb.write_text("placeholder", encoding="utf-8")

            result = CliRunner().invoke(
                app,
                [
                    "run",
                    str(glb),
                    "--config",
                    str(ROOT / "configs" / "default.yaml"),
                    "--profile",
                    "server",
                    "--output-dir",
                    str(output_root),
                    "--mask-scale",
                    "2.0",
                    "--dry-run",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Profile: server", result.output)
            manifests = list(output_root.glob("*/manifest.json"))
            self.assertEqual(len(manifests), 1)
            saved = json.loads(manifests[0].read_text(encoding="utf-8"))
            self.assertEqual(saved["mask_scale"], "2.0")
            self.assertEqual(saved["status"], "dry_run_prepared")

    def test_batch_command_loads_profile_and_counts_glbs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            (temp_root / "a.glb").write_text("a", encoding="utf-8")
            (temp_root / "b.glb").write_text("b", encoding="utf-8")
            (temp_root / "ignore.txt").write_text("x", encoding="utf-8")

            result = CliRunner().invoke(
                app,
                [
                    "batch",
                    str(temp_root),
                    "--config",
                    str(ROOT / "configs" / "default.yaml"),
                    "--profile",
                    "local_wsl",
                    "--dry-run",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Profile: local_wsl", result.output)
            self.assertIn("GLB count: 2", result.output)
            self.assertIn("Dry run: True", result.output)

    def test_bridge_command_converts_existing_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            run_dir = temp_root / "demo-20260515-120000"
            sam_dir = run_dir / "sam"
            sam_dir.mkdir(parents=True)
            mesh = trimesh.creation.box()
            staged_glb = sam_dir / f"{run_dir.name}.glb"
            mesh.export(staged_glb)
            np.save(sam_dir / "mesh_1.0.npy", np.zeros(len(mesh.faces), dtype=int))
            manifest = {
                "input_path": str(staged_glb),
                "profile": "local_wsl",
                "output_root": str(temp_root),
                "run_dir": str(run_dir),
                "mask_scale": "1.0",
                "status": "sampart3d_complete",
                "created_at": "2026-05-15T12:00:00",
                "updated_at": "2026-05-15T12:00:00",
                "paths": {
                    "run_dir": str(run_dir),
                    "logs_dir": str(run_dir / "logs"),
                    "sam_dir": str(sam_dir),
                    "bridge_dir": str(run_dir / "bridge"),
                    "prepared_dir": str(run_dir / "prepared"),
                    "holopart_dir": str(run_dir / "holopart"),
                    "manifest_path": str(run_dir / "manifest.json"),
                },
                "commands": [],
                "sampart3d": {
                    "paths": {"mesh_path": str(staged_glb), "selected_mask": str(sam_dir / "mesh_1.0.npy")},
                    "copied_selected_mask": str(sam_dir / "mesh_1.0.npy"),
                },
            }
            (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            result = CliRunner().invoke(
                app,
                [
                    "bridge",
                    str(run_dir),
                    "--config",
                    str(ROOT / "configs" / "default.yaml"),
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Status: bridge_complete", result.output)
            self.assertTrue((run_dir / "bridge" / "prepared_parts.glb").exists())
            updated = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("sampart3d", updated)
            self.assertIn("bridge", updated)


if __name__ == "__main__":
    unittest.main()

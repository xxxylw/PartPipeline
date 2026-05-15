from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()

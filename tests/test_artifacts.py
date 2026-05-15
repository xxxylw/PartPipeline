from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.artifacts import create_run_paths, write_manifest
from partpipeline.types import RunManifest


class ArtifactTests(unittest.TestCase):
    def test_create_run_paths_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            paths = create_run_paths(
                Path("/assets/fancy chair.glb"),
                output_root,
                timestamp="20260515-120000",
            )

            self.assertEqual(paths.run_dir.name, "fancy-chair-20260515-120000")
            self.assertTrue(paths.logs_dir.is_dir())
            self.assertTrue(paths.sam_dir.is_dir())
            self.assertTrue(paths.prepared_dir.is_dir())
            self.assertTrue(paths.holopart_dir.is_dir())

            manifest = RunManifest(
                input_path=Path("/assets/fancy chair.glb"),
                profile="local_wsl",
                output_root=output_root,
                run_dir=paths.run_dir,
                mask_scale="1.0",
                status="dry_run_prepared",
                created_at="2026-05-15T12:00:00",
                updated_at="2026-05-15T12:00:00",
                paths=paths,
                commands=[],
            )

            write_manifest(manifest)
            saved = json.loads(paths.manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(saved["input_path"], "/assets/fancy chair.glb")
            self.assertEqual(saved["profile"], "local_wsl")
            self.assertEqual(saved["mask_scale"], "1.0")
            self.assertEqual(saved["paths"]["logs_dir"], str(paths.logs_dir))


if __name__ == "__main__":
    unittest.main()

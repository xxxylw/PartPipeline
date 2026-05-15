from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.orchestrator import prepare_single_run
from partpipeline.types import RunRequest


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


if __name__ == "__main__":
    unittest.main()

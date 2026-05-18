from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.inputs import stage_glb_inputs
from partpipeline.types import InputManifest, StagedInputItem


class InputStagingTests(unittest.TestCase):
    def test_stage_glb_inputs_copies_only_glbs_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            destination = root / "inputs" / "phase7"
            source.mkdir()
            first = source / "01.测试 sofa.glb"
            second = source / "02.tree.glb"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            (source / "ignore.txt").write_text("ignore", encoding="utf-8")

            manifest = stage_glb_inputs(source, destination, limit=1)

            self.assertIsInstance(manifest, InputManifest)
            self.assertIsInstance(manifest.items[0], StagedInputItem)
            self.assertEqual(len(manifest.items), 1)
            self.assertEqual(manifest.items[0].asset_name, "01.测试 sofa.glb")
            self.assertTrue((destination / "01.测试 sofa.glb").exists())
            self.assertFalse((destination / "02.tree.glb").exists())
            self.assertFalse((destination / "ignore.txt").exists())
            saved = json.loads((destination / "input_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["source_dir"], str(source.resolve()))
            self.assertEqual(saved["destination_dir"], str(destination.resolve()))
            self.assertEqual(saved["items"][0]["source_path"], str(first.resolve()))
            self.assertEqual(saved["items"][0]["staged_path"], str((destination / first.name).resolve()))


if __name__ == "__main__":
    unittest.main()

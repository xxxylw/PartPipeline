from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.presentation import PresentationPackagingError, package_batch, package_run
from partpipeline.types import (
    PresentationBatchItem,
    PresentationBatchManifest,
    PresentationLevel,
    PresentationPackageManifest,
)


def make_run(root: Path, name: str = "demo-run", with_level_b: bool = True) -> Path:
    run_dir = root / name
    bridge_dir = run_dir / "bridge"
    holopart_dir = run_dir / "holopart"
    bridge_dir.mkdir(parents=True)
    holopart_dir.mkdir()
    original = root / "original.glb"
    original.write_bytes(b"original")
    prepared = bridge_dir / "prepared_parts.glb"
    prepared.write_bytes(b"level-a")
    part_manifest = bridge_dir / "part_manifest.json"
    part_manifest.write_text('{"parts":[]}', encoding="utf-8")
    holopart_data = None
    if with_level_b:
        output = holopart_dir / "output.glb"
        output.write_bytes(b"level-b")
        holopart_data = {"output_glb": str(output)}
    manifest = {
        "input_path": str(original),
        "profile": "local_wsl",
        "output_root": str(root),
        "run_dir": str(run_dir),
        "mask_scale": "1.0",
        "status": "holopart_complete" if with_level_b else "bridge_complete",
        "created_at": "2026-05-19T12:00:00",
        "updated_at": "2026-05-19T12:00:00",
        "paths": {
            "run_dir": str(run_dir),
            "bridge_dir": str(bridge_dir),
            "holopart_dir": str(holopart_dir),
            "manifest_path": str(run_dir / "manifest.json"),
        },
        "bridge": {"prepared_glb": str(prepared), "part_manifest": str(part_manifest)},
    }
    if holopart_data is not None:
        manifest["holopart"] = holopart_data
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run_dir


class PresentationTypeTests(unittest.TestCase):
    def test_package_manifest_serializes_paths_and_default_level(self) -> None:
        level = PresentationLevel(
            level="A",
            name="segmented_parts",
            source_path=Path("/source.glb"),
            package_path=Path("/package.glb"),
            recommended_for_display=True,
            role="default_display",
        )
        manifest = PresentationPackageManifest(
            package_dir=Path("/pkg"),
            source_run_dir=Path("/run"),
            source_manifest=Path("/run/manifest.json"),
            input_path=Path("/input.glb"),
            default_level="A",
            levels=[level],
            part_manifest=None,
            original_glb=None,
            notes=["note"],
            manifest_path=Path("/pkg/presentation_manifest.json"),
        )

        saved = manifest.to_dict()

        self.assertEqual(saved["default_level"], "A")
        self.assertEqual(saved["levels"][0]["source_path"], "/source.glb")
        self.assertTrue(saved["levels"][0]["recommended_for_display"])

    def test_batch_manifest_counts_items(self) -> None:
        manifest = PresentationBatchManifest(
            batch_manifest_path=Path("/batch.json"),
            presentation_dir=Path("/presentation"),
            manifest_path=Path("/presentation/presentation_batch_manifest.json"),
            items=[
                PresentationBatchItem("a.glb", Path("/a/manifest.json"), Path("/a"), Path("/a/presentation_manifest.json"), "packaged"),
                PresentationBatchItem("b.glb", None, None, None, "failed", {"type": "test", "message": "boom"}),
            ],
        )

        saved = manifest.to_dict()

        self.assertEqual(saved["total"], 2)
        self.assertEqual(saved["packaged"], 1)
        self.assertEqual(saved["failed"], 1)


class PresentationPackagingTests(unittest.TestCase):
    def test_package_run_defaults_to_level_a_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_run(root, "02.-01-20260518-190552")

            manifest = package_run(run_dir, root / "presentation")

            self.assertEqual(manifest.package_dir.name, "02.-01-20260518-190552")
            self.assertTrue((manifest.package_dir / "level_a_segmented_parts.glb").exists())
            self.assertFalse((manifest.package_dir / "level_b_holopart_output.glb").exists())
            self.assertTrue((manifest.package_dir / "part_manifest.json").exists())
            saved = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["default_level"], "A")
            self.assertTrue(saved["levels"][0]["recommended_for_display"])
            self.assertEqual(saved["levels"][0]["level"], "A")
            self.assertEqual(saved["original_glb"], None)

    def test_package_run_can_include_level_b_and_original(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_run(root)

            manifest = package_run(
                run_dir,
                root / "presentation",
                include_level_b=True,
                include_original=True,
            )

            self.assertTrue((manifest.package_dir / "level_b_holopart_output.glb").exists())
            self.assertTrue((manifest.package_dir / "original.glb").exists())
            saved = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual([level["level"] for level in saved["levels"]], ["A", "B"])
            self.assertFalse(saved["levels"][1]["recommended_for_display"])

    def test_package_run_fails_when_level_a_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_run(root)
            (run_dir / "bridge" / "prepared_parts.glb").unlink()

            with self.assertRaisesRegex(PresentationPackagingError, "Level A"):
                package_run(run_dir, root / "presentation")

    def test_package_run_fails_when_requested_level_b_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_run(root, with_level_b=False)

            with self.assertRaisesRegex(PresentationPackagingError, "Level B"):
                package_run(run_dir, root / "presentation", include_level_b=True)

    def test_package_batch_records_successes_and_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_run(root, "asset-a-run")
            batch_dir = root / "runs" / "batches" / "batch-test"
            batch_dir.mkdir(parents=True)
            missing = root / "missing" / "manifest.json"
            batch_manifest = batch_dir / "batch_manifest.json"
            batch_manifest.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "asset_name": "a.glb",
                                "manifest_path": str(run_dir / "manifest.json"),
                            },
                            {
                                "asset_name": "missing.glb",
                                "manifest_path": str(missing),
                            },
                            {
                                "asset_name": "failed.glb",
                                "manifest_path": None,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            manifest = package_batch(batch_manifest, root / "presentation")

            self.assertEqual(manifest.total, 3)
            self.assertEqual(manifest.packaged, 1)
            self.assertEqual(manifest.failed, 2)
            self.assertTrue((root / "presentation" / "presentation_batch_manifest.json").exists())
            self.assertTrue((manifest.items[0].package_dir / "level_a_segmented_parts.glb").exists())


if __name__ == "__main__":
    unittest.main()

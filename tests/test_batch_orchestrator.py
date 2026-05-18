from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.artifacts import write_batch_manifest
from partpipeline.orchestrator import run_batch_pipeline
from partpipeline.types import BatchItemResult, BatchManifest, RunManifest, RunPaths


def make_manifest(glb: Path, output_root: Path, status: str = "bridge_complete") -> RunManifest:
    run_dir = output_root / f"{glb.stem}-run"
    paths = RunPaths(
        run_dir=run_dir,
        logs_dir=run_dir / "logs",
        sam_dir=run_dir / "sam",
        bridge_dir=run_dir / "bridge",
        prepared_dir=run_dir / "prepared",
        holopart_dir=run_dir / "holopart",
        manifest_path=run_dir / "manifest.json",
    )
    for directory in (paths.logs_dir, paths.sam_dir, paths.bridge_dir, paths.prepared_dir, paths.holopart_dir):
        directory.mkdir(parents=True, exist_ok=True)
    manifest = RunManifest(
        input_path=glb,
        profile="local_wsl",
        output_root=output_root,
        run_dir=run_dir,
        mask_scale="1.0",
        status=status,
        created_at="2026-05-18T12:00:00",
        updated_at="2026-05-18T12:00:00",
        paths=paths,
    )
    paths.manifest_path.write_text(json.dumps(manifest.to_dict()), encoding="utf-8")
    return manifest


class BatchOrchestratorTests(unittest.TestCase):
    def test_batch_manifest_counts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = BatchManifest(
                batch_id="batch-20260518-120000",
                profile="local_wsl",
                input_dir=root / "inputs",
                output_root=root / "runs",
                mask_scale="1.0",
                status="partial",
                created_at="2026-05-18T12:00:00",
                updated_at="2026-05-18T12:00:00",
                manifest_path=root / "runs" / "batches" / "batch-20260518-120000" / "batch_manifest.json",
                items=[
                    BatchItemResult("a.glb", root / "a.glb", None, root / "run-a", root / "run-a" / "manifest.json", "holopart_complete"),
                    BatchItemResult("b.glb", root / "b.glb", None, None, None, "failed", {"type": "test", "message": "boom"}),
                ],
            )

            write_batch_manifest(manifest)

            saved = json.loads(manifest.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["total"], 2)
            self.assertEqual(saved["succeeded"], 1)
            self.assertEqual(saved["failed"], 1)
            self.assertEqual(len(saved["items"]), 2)

    def test_run_batch_pipeline_records_success_and_source_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = root / "inputs"
            output_root = root / "runs"
            inputs.mkdir()
            source = root / "originals" / "a.glb"
            source.parent.mkdir()
            glb = inputs / "a.glb"
            glb.write_bytes(b"glb")
            (inputs / "input_manifest.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "asset_name": "a.glb",
                                "source_path": str(source),
                                "staged_path": str(glb.resolve()),
                                "size_bytes": 3,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            def fake_single_run(request):
                return make_manifest(request.input_path, output_root)

            def fake_holopart(run_dir, config_path, profile_name=None):
                return make_manifest(glb, output_root, status="holopart_complete")

            manifest = run_batch_pipeline(
                inputs,
                ROOT / "configs" / "default.yaml",
                output_dir=output_root,
                single_run_func=fake_single_run,
                holopart_func=fake_holopart,
            )

            self.assertEqual(manifest.status, "complete")
            self.assertEqual(manifest.items[0].status, "holopart_complete")
            self.assertEqual(manifest.items[0].source_path, source)
            self.assertTrue(manifest.manifest_path.exists())

    def test_run_batch_pipeline_continues_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = root / "inputs"
            output_root = root / "runs"
            inputs.mkdir()
            (inputs / "a.glb").write_bytes(b"a")
            (inputs / "b.glb").write_bytes(b"b")

            def fake_single_run(request):
                if request.input_path.name == "a.glb":
                    raise RuntimeError("broken")
                return make_manifest(request.input_path, output_root, status="holopart_complete")

            manifest = run_batch_pipeline(
                inputs,
                ROOT / "configs" / "default.yaml",
                output_dir=output_root,
                single_run_func=fake_single_run,
                run_holopart=False,
            )

            self.assertEqual(manifest.status, "partial")
            self.assertEqual([item.status for item in manifest.items], ["failed", "holopart_complete"])

    def test_run_batch_pipeline_dry_run_skips_holopart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = root / "inputs"
            output_root = root / "runs"
            inputs.mkdir()
            (inputs / "a.glb").write_bytes(b"a")
            holopart_calls = []

            def fake_single_run(request):
                return make_manifest(request.input_path, output_root, status="dry_run_prepared")

            def fake_holopart(*args, **kwargs):
                holopart_calls.append(args)
                raise AssertionError("HoloPart should not run during dry-run")

            manifest = run_batch_pipeline(
                inputs,
                ROOT / "configs" / "default.yaml",
                output_dir=output_root,
                dry_run=True,
                single_run_func=fake_single_run,
                holopart_func=fake_holopart,
            )

            self.assertEqual(manifest.status, "dry_run")
            self.assertEqual(len(holopart_calls), 0)

    def test_run_batch_pipeline_empty_input_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = root / "inputs"
            inputs.mkdir()

            manifest = run_batch_pipeline(inputs, ROOT / "configs" / "default.yaml", output_dir=root / "runs")

            self.assertEqual(manifest.status, "empty")
            self.assertEqual(manifest.items, [])


if __name__ == "__main__":
    unittest.main()

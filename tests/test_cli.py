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


def make_packagable_run(root: Path, name: str = "demo-run", with_level_b: bool = True) -> Path:
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
    manifest = {
        "input_path": str(original),
        "profile": "local_wsl",
        "output_root": str(root),
        "run_dir": str(run_dir),
        "mask_scale": "1.0",
        "status": "bridge_complete",
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
    if with_level_b:
        output = holopart_dir / "output.glb"
        output.write_bytes(b"level-b")
        manifest["holopart"] = {"output_glb": str(output)}
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return run_dir


class CliTests(unittest.TestCase):
    def test_stage_inputs_command_copies_glbs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            source = temp_root / "source"
            destination = temp_root / "inputs" / "phase7"
            source.mkdir()
            (source / "01.测试 sofa.glb").write_bytes(b"glb")
            (source / "ignore.txt").write_text("x", encoding="utf-8")

            result = CliRunner().invoke(
                app,
                [
                    "stage-inputs",
                    str(source),
                    "--destination",
                    str(destination),
                    "--limit",
                    "1",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("GLB count: 1", result.output)
            self.assertIn("Input manifest:", result.output)
            self.assertTrue((destination / "01.测试 sofa.glb").exists())
            self.assertTrue((destination / "input_manifest.json").exists())

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
            self.assertIn("Status: dry_run", result.output)
            self.assertIn("Total: 2", result.output)
            self.assertIn("Batch manifest:", result.output)

    def test_package_command_writes_level_a_package_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_packagable_run(root)
            presentation = root / "presentation"

            result = CliRunner().invoke(
                app,
                ["package", str(run_dir), "--presentation-dir", str(presentation)],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Default level: A", result.output)
            package_dir = presentation / "original"
            self.assertTrue((package_dir / "level_a_segmented_parts.glb").exists())
            self.assertFalse((package_dir / "level_b_holopart_output.glb").exists())
            saved = json.loads((package_dir / "presentation_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["default_level"], "A")

    def test_package_command_can_include_level_b(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_packagable_run(root)
            presentation = root / "presentation"

            result = CliRunner().invoke(
                app,
                [
                    "package",
                    str(run_dir),
                    "--presentation-dir",
                    str(presentation),
                    "--include-level-b",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue((presentation / "original" / "level_b_holopart_output.glb").exists())

    def test_package_command_reports_missing_level_a(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_packagable_run(root)
            (run_dir / "bridge" / "prepared_parts.glb").unlink()

            result = CliRunner().invoke(
                app,
                ["package", str(run_dir), "--presentation-dir", str(root / "presentation")],
            )

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Level A", result.output)

    def test_package_batch_command_writes_batch_presentation_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = make_packagable_run(root, "asset-a-run")
            batch_dir = root / "runs" / "batches" / "batch-test"
            batch_dir.mkdir(parents=True)
            batch_manifest = batch_dir / "batch_manifest.json"
            batch_manifest.write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "asset_name": "a.glb",
                                "manifest_path": str(run_dir / "manifest.json"),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            presentation = root / "presentation"

            result = CliRunner().invoke(
                app,
                ["package-batch", str(batch_manifest), "--presentation-dir", str(presentation)],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Packaged: 1", result.output)
            self.assertTrue((presentation / "presentation_batch_manifest.json").exists())

    def test_animate_command_exports_parts_and_video(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = root / "presentation" / "demo"
            package_dir.mkdir(parents=True)
            scene = trimesh.Scene()
            scene.add_geometry(trimesh.creation.box(), geom_name="part_a")
            scene.add_geometry(trimesh.creation.icosphere(subdivisions=0), geom_name="part_b")
            level_a = package_dir / "level_a_segmented_parts.glb"
            scene.export(level_a)
            (package_dir / "presentation_manifest.json").write_text(
                json.dumps({"levels": [{"level": "A", "package_path": str(level_a)}]}),
                encoding="utf-8",
            )
            blender = root / "fake_blender.sh"
            ffmpeg = root / "fake_ffmpeg.sh"
            blender.write_text(
                "#!/usr/bin/env bash\n"
                "if [ \"$1\" = \"--version\" ]; then echo 'Blender 4.5.0'; exit 0; fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            ffmpeg.write_text(
                "#!/usr/bin/env bash\n"
                "if [ \"$1\" = \"-version\" ]; then echo 'ffmpeg version 8.0.1'; exit 0; fi\n"
                "out=\"${@: -1}\"\n"
                "mkdir -p \"$(dirname \"$out\")\"\n"
                "printf mp4 > \"$out\"\n",
                encoding="utf-8",
            )
            blender.chmod(0o755)
            ffmpeg.chmod(0o755)

            result = CliRunner().invoke(
                app,
                [
                    "animate",
                    str(package_dir),
                    "--config",
                    str(ROOT / "configs" / "default.yaml"),
                    "--blender-path",
                    str(blender),
                    "--ffmpeg-path",
                    str(ffmpeg),
                    "--duration-seconds",
                    "1",
                    "--fps",
                    "2",
                ],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Video:", result.output)
            self.assertTrue((package_dir / "parts" / "part_001.glb").exists())
            self.assertTrue((package_dir / "animation" / "exploded_assembly.mp4").exists())

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

    def test_holopart_command_fails_when_prepared_glb_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            (run_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "input_path": "missing.glb",
                        "profile": "local_wsl",
                        "output_root": str(run_dir.parent),
                        "run_dir": str(run_dir),
                        "mask_scale": "1.0",
                        "status": "bridge_complete",
                        "created_at": "2026-05-15T12:00:00",
                        "updated_at": "2026-05-15T12:00:00",
                        "paths": {
                            "run_dir": str(run_dir),
                            "logs_dir": str(run_dir / "logs"),
                            "sam_dir": str(run_dir / "sam"),
                            "bridge_dir": str(run_dir / "bridge"),
                            "prepared_dir": str(run_dir / "prepared"),
                            "holopart_dir": str(run_dir / "holopart"),
                            "manifest_path": str(run_dir / "manifest.json"),
                        },
                        "commands": [],
                    }
                ),
                encoding="utf-8",
            )

            result = CliRunner().invoke(
                app,
                [
                    "holopart",
                    str(run_dir),
                    "--config",
                    str(ROOT / "configs" / "default.yaml"),
                ],
            )

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("prepared_parts.glb", result.output)


if __name__ == "__main__":
    unittest.main()

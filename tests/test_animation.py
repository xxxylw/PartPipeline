from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Sequence

import trimesh


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.animation import (  # noqa: E402
    AnimationGenerationError,
    export_parts,
    render_exploded_animation,
    resolve_level_a_path,
)
from partpipeline.types import AnimationToolStatus, PartExportItem, PartExportManifest  # noqa: E402


class FakeResult:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def make_package(root: Path) -> Path:
    package_dir = root / "presentation" / "demo"
    package_dir.mkdir(parents=True)
    scene = trimesh.Scene()
    scene.add_geometry(trimesh.creation.box(extents=(1, 1, 1)), geom_name="part_a")
    scene.add_geometry(trimesh.creation.box(extents=(0.5, 0.5, 0.5)), geom_name="part_b")
    level_a = package_dir / "level_a_segmented_parts.glb"
    scene.export(level_a)
    (package_dir / "presentation_manifest.json").write_text(
        json.dumps(
            {
                "default_level": "A",
                "levels": [
                    {
                        "level": "A",
                        "package_path": str(level_a),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return package_dir


class AnimationTypeTests(unittest.TestCase):
    def test_part_export_manifest_serializes_counts(self) -> None:
        item = PartExportItem(
            index=1,
            name="part_001",
            source_geometry="geom",
            path=Path("/tmp/part_001.glb"),
            centroid=[0.0, 0.0, 0.0],
            bounds=[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
            vertex_count=8,
            face_count=12,
        )
        manifest = PartExportManifest(
            package_dir=Path("/pkg"),
            source_level_a=Path("/pkg/level_a_segmented_parts.glb"),
            parts_dir=Path("/pkg/parts"),
            items=[item],
            manifest_path=Path("/pkg/parts/parts_manifest.json"),
        )

        saved = manifest.to_dict()

        self.assertEqual(saved["total"], 1)
        self.assertEqual(saved["items"][0]["name"], "part_001")

    def test_animation_tool_status_serializes_versions(self) -> None:
        status = AnimationToolStatus(Path("/bin/blender"), Path("/bin/ffmpeg"), "Blender 4.5", "ffmpeg 8")

        saved = status.to_dict()

        self.assertEqual(saved["blender_version"], "Blender 4.5")
        self.assertEqual(saved["ffmpeg_path"], "/bin/ffmpeg")


class AnimationExportTests(unittest.TestCase):
    def test_resolves_level_a_from_presentation_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = make_package(Path(temp_dir))

            self.assertEqual(resolve_level_a_path(package_dir), package_dir / "level_a_segmented_parts.glb")

    def test_export_parts_writes_individual_glbs_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = make_package(Path(temp_dir))

            manifest = export_parts(package_dir)

            self.assertEqual(manifest.total, 2)
            self.assertTrue((package_dir / "parts" / "part_001.glb").exists())
            self.assertTrue((package_dir / "parts" / "part_002.glb").exists())
            self.assertTrue((package_dir / "parts" / "parts_manifest.json").exists())

    def test_missing_level_a_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "package"
            package_dir.mkdir()

            with self.assertRaisesRegex(AnimationGenerationError, "Level A"):
                export_parts(package_dir)

    def test_render_uses_blender_then_ffmpeg_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package_dir = make_package(root)
            blender = root / "blender"
            ffmpeg = root / "ffmpeg"
            blender.write_text("", encoding="utf-8")
            ffmpeg.write_text("", encoding="utf-8")
            commands: list[list[str]] = []

            def fake_runner(command: Sequence[str], **kwargs):
                command_list = [str(value) for value in command]
                commands.append(command_list)
                if command_list[1:] == ["--version"]:
                    return FakeResult(stdout="Blender 4.5.0\n")
                if command_list[1:] == ["-version"]:
                    return FakeResult(stdout="ffmpeg version 8.0.1\n")
                if "--python" in command_list:
                    frames = package_dir / "animation" / "frames"
                    frames.mkdir(parents=True, exist_ok=True)
                    (frames / "frame_0001.png").write_bytes(b"png")
                    return FakeResult()
                if "-framerate" in command_list:
                    (package_dir / "animation" / "exploded_assembly.mp4").write_bytes(b"mp4")
                    return FakeResult()
                return FakeResult()

            manifest = render_exploded_animation(
                package_dir,
                blender_path=blender,
                ffmpeg_path=ffmpeg,
                duration_seconds=1.0,
                fps=2,
                runner=fake_runner,
            )

            self.assertEqual(manifest.frame_count, 2)
            self.assertTrue(manifest.video_path.exists())
            self.assertTrue(manifest.manifest_path.exists())
            self.assertTrue(any("--python" in command for command in commands))
            self.assertTrue(any("-framerate" in command for command in commands))


if __name__ == "__main__":
    unittest.main()

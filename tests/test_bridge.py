from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from partpipeline.artifacts import create_run_paths
from partpipeline.bridge import BridgeConverter, BridgeConversionError, merge_small_parts, validate_face_mask
from partpipeline.types import BridgeConfig


def two_square_mesh() -> trimesh.Trimesh:
    vertices = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [2, 0, 0],
            [0, 1, 0],
            [1, 1, 0],
            [2, 1, 0],
        ],
        dtype=float,
    )
    faces = np.array(
        [
            [0, 1, 3],
            [1, 4, 3],
            [1, 2, 4],
            [2, 5, 4],
        ],
        dtype=int,
    )
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


class BridgeTests(unittest.TestCase):
    def test_validate_face_mask_rejects_face_count_mismatch(self) -> None:
        mesh = two_square_mesh()

        with self.assertRaisesRegex(BridgeConversionError, "face count"):
            validate_face_mask(mesh, np.array([0, 1, 1]))

    def test_merge_small_part_uses_shared_boundary_neighbor(self) -> None:
        mesh = two_square_mesh()
        original = np.array([1, 0, 0, 0])
        merged, records = merge_small_parts(
            mesh,
            original,
            BridgeConfig(merge_small_parts=True, min_faces_per_part=2, min_area_ratio=0.0),
        )

        self.assertEqual(merged.tolist(), [0, 0, 0, 0])
        self.assertEqual(original.tolist(), [1, 0, 0, 0])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].source_label, 1)
        self.assertEqual(records[0].target_label, 0)
        self.assertEqual(records[0].method, "topology")

    def test_convert_exports_multipart_glb_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            mesh = two_square_mesh()
            glb = root / "input.glb"
            mesh.export(glb)
            mask = root / "mesh_1.0.npy"
            np.save(mask, np.array([1, 0, 0, 2]))
            paths = create_run_paths(glb, root / "runs", timestamp="20260515-120000")

            result = BridgeConverter(
                BridgeConfig(merge_small_parts=True, min_faces_per_part=2, min_area_ratio=0.0)
            ).convert(glb, mask, paths, "1.0")

            self.assertTrue(result.prepared_glb.exists())
            self.assertTrue(result.merged_mask.exists())
            self.assertTrue(result.part_manifest.exists())
            saved_mask = np.load(result.merged_mask)
            self.assertEqual(saved_mask.tolist(), [0, 0, 0, 0])
            saved = json.loads(result.part_manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved["original_part_count"], 3)
            self.assertEqual(saved["final_part_count"], 1)
            self.assertEqual(len(saved["merge_history"]), 2)
            loaded = trimesh.load(result.prepared_glb)
            self.assertGreaterEqual(len(getattr(loaded, "geometry", {})), 1)



from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import trimesh

from partpipeline.artifacts import bridge_artifact_paths
from partpipeline.types import BridgeConfig, BridgeMergeRecord, BridgePartStats, BridgeResult, RunPaths


class BridgeConversionError(RuntimeError):
    """Raised when SAMPart3D output cannot be converted for HoloPart."""


def validate_face_mask(mesh: trimesh.Trimesh, mask: np.ndarray) -> np.ndarray:
    mask = np.asarray(mask)
    if mask.ndim != 1:
        raise BridgeConversionError(f"Mask must be one-dimensional, got shape {mask.shape}")
    face_count = len(mesh.faces)
    if len(mask) != face_count:
        raise BridgeConversionError(
            f"Mask face count mismatch: mask has {len(mask)} labels but mesh has {face_count} faces"
        )
    if not np.issubdtype(mask.dtype, np.integer):
        if not np.all(np.equal(mask, mask.astype(np.int64))):
            raise BridgeConversionError(f"Mask labels must be integers, got dtype {mask.dtype}")
    return mask.astype(np.int64, copy=True)


def merge_small_parts(
    mesh: trimesh.Trimesh,
    mask: np.ndarray,
    config: BridgeConfig,
) -> tuple[np.ndarray, list[BridgeMergeRecord]]:
    merged = validate_face_mask(mesh, mask)
    if not config.merge_small_parts:
        return merged, []

    labels, counts = np.unique(merged, return_counts=True)
    total_faces = max(1, len(merged))
    small_labels = {
        int(label)
        for label, count in zip(labels, counts)
        if int(count) < config.min_faces_per_part or (float(count) / total_faces) < config.min_area_ratio
    }
    if not small_labels or len(small_labels) == len(labels):
        return merged, []

    records: list[BridgeMergeRecord] = []
    for source_label in sorted(small_labels):
        large_labels = sorted(set(int(label) for label in np.unique(merged)) - small_labels)
        if not large_labels:
            break
        source_faces = np.where(merged == source_label)[0]
        if len(source_faces) == 0:
            continue
        boundary_counts = _boundary_counts(mesh, merged, source_label, set(large_labels))
        if boundary_counts:
            target_label, boundary_count = sorted(boundary_counts.items(), key=lambda item: (-item[1], item[0]))[0]
            merged[source_faces] = target_label
            records.append(
                BridgeMergeRecord(
                    source_label=source_label,
                    target_label=int(target_label),
                    method="topology",
                    reason="small_part_shared_boundary",
                    face_count=int(len(source_faces)),
                    boundary_count=int(boundary_count),
                )
            )
            continue

        target_label, distance = _nearest_label_by_centroid(mesh, merged, source_label, large_labels)
        merged[source_faces] = target_label
        records.append(
            BridgeMergeRecord(
                source_label=source_label,
                target_label=int(target_label),
                method="nearest",
                reason="small_part_no_topology_neighbor",
                face_count=int(len(source_faces)),
                distance=float(distance),
            )
        )

    return merged, records


class BridgeConverter:
    def __init__(self, config: BridgeConfig | None = None) -> None:
        self.config = config or BridgeConfig()

    def convert(self, glb_path: Path, mask_path: Path, run_paths: RunPaths, mask_scale: str) -> BridgeResult:
        glb_path = glb_path.expanduser().resolve()
        mask_path = mask_path.expanduser().resolve()
        if not glb_path.exists():
            raise BridgeConversionError(f"Source GLB does not exist: {glb_path}")
        if not mask_path.exists():
            raise BridgeConversionError(f"SAMPart3D mask does not exist: {mask_path}")

        loaded = trimesh.load(glb_path, force="mesh")
        if not isinstance(loaded, trimesh.Trimesh):
            raise BridgeConversionError(f"Could not load GLB as a mesh: {glb_path}")
        source_mask = validate_face_mask(loaded, np.load(mask_path))
        merged_mask, merge_history = merge_small_parts(loaded, source_mask, self.config)
        part_stats = _part_stats(loaded, merged_mask, merge_history)
        output_paths = bridge_artifact_paths(run_paths, mask_scale)
        run_paths.bridge_dir.mkdir(parents=True, exist_ok=True)

        scene = trimesh.Scene()
        for index, label in enumerate(sorted(int(label) for label in np.unique(merged_mask))):
            part_mesh = loaded.submesh([merged_mask == label], append=True, repair=False)
            if part_mesh is None or len(part_mesh.faces) == 0:
                continue
            name = f"part_{index:03d}_label_{label}"
            part_mesh.metadata["name"] = name
            scene.add_geometry(part_mesh, node_name=name, geom_name=name)

        if not scene.geometry:
            raise BridgeConversionError("No part geometries were produced")

        np.save(output_paths["merged_mask"], merged_mask)
        scene.export(output_paths["prepared_glb"])
        result = BridgeResult(
            source_glb=glb_path,
            source_mask=mask_path,
            prepared_glb=output_paths["prepared_glb"],
            merged_mask=output_paths["merged_mask"],
            part_manifest=output_paths["part_manifest"],
            original_part_count=int(len(np.unique(source_mask))),
            final_part_count=int(len(np.unique(merged_mask))),
            parts=part_stats,
            merge_history=merge_history,
        )
        output_paths["part_manifest"].write_text(
            json.dumps(
                {
                    **result.to_dict(),
                    "validation": {
                        "face_count": int(len(loaded.faces)),
                        "mask_face_count": int(len(source_mask)),
                        "compatible": True,
                    },
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return result


def _boundary_counts(
    mesh: trimesh.Trimesh,
    mask: np.ndarray,
    source_label: int,
    candidate_labels: set[int],
) -> Counter[int]:
    counts: Counter[int] = Counter()
    edge_faces: dict[tuple[int, int], list[int]] = defaultdict(list)
    for face_index, face in enumerate(mesh.faces):
        vertices = [int(face[0]), int(face[1]), int(face[2])]
        for edge in (
            tuple(sorted((vertices[0], vertices[1]))),
            tuple(sorted((vertices[1], vertices[2]))),
            tuple(sorted((vertices[2], vertices[0]))),
        ):
            edge_faces[edge].append(face_index)

    for faces in edge_faces.values():
        if len(faces) < 2:
            continue
        source_faces = [face for face in faces if int(mask[face]) == source_label]
        if not source_faces:
            continue
        for face in faces:
            label = int(mask[face])
            if label in candidate_labels:
                counts[label] += len(source_faces)
    return counts


def _nearest_label_by_centroid(
    mesh: trimesh.Trimesh,
    mask: np.ndarray,
    source_label: int,
    candidate_labels: list[int],
) -> tuple[int, float]:
    source_centroid = _label_centroid(mesh, mask, source_label)
    best_label = candidate_labels[0]
    best_distance = float("inf")
    for label in candidate_labels:
        distance = float(np.linalg.norm(source_centroid - _label_centroid(mesh, mask, label)))
        if distance < best_distance or (distance == best_distance and label < best_label):
            best_label = label
            best_distance = distance
    return best_label, best_distance


def _label_centroid(mesh: trimesh.Trimesh, mask: np.ndarray, label: int) -> np.ndarray:
    face_indices = np.where(mask == label)[0]
    triangles = mesh.triangles[face_indices]
    return triangles.reshape(-1, 3).mean(axis=0)


def _part_stats(
    mesh: trimesh.Trimesh,
    mask: np.ndarray,
    merge_history: list[BridgeMergeRecord],
) -> list[BridgePartStats]:
    total_faces = max(1, len(mask))
    area_faces = getattr(mesh, "area_faces", np.zeros(len(mask), dtype=float))
    merged_from: dict[int, list[int]] = defaultdict(list)
    for record in merge_history:
        merged_from[int(record.target_label)].append(int(record.source_label))

    stats: list[BridgePartStats] = []
    for index, label in enumerate(sorted(int(label) for label in np.unique(mask))):
        face_indices = np.where(mask == label)[0]
        stats.append(
            BridgePartStats(
                label=label,
                name=f"part_{index:03d}_label_{label}",
                face_count=int(len(face_indices)),
                face_ratio=float(len(face_indices) / total_faces),
                area=float(np.asarray(area_faces)[face_indices].sum()) if len(face_indices) else 0.0,
                merged_from=sorted(merged_from.get(label, [])),
            )
        )
    return stats

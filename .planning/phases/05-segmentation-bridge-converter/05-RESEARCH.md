# Phase 5 Research: Segmentation Bridge Converter

## Goal

Convert a SAMPart3D face mask and source GLB into a HoloPart-compatible multipart GLB.

## Findings

### HoloPart Input Format

HoloPart's README defines the bridge pattern directly:

```python
import trimesh
import numpy as np

mesh = trimesh.load("mesh.glb", force="mesh")
mask_npy = np.load("mask.npy")
mesh_parts = []
for part_id in np.unique(mask_npy):
    mesh_part = mesh.submesh([mask_npy == part_id], append=True)
    mesh_parts.append(mesh_part)
mesh_parts = trimesh.Scene(mesh_parts).export("input_mesh.glb")
```

`third_party/HoloPart/scripts/inference_holopart.py` loads a `.glb` with:

```python
parts_mesh = trimesh.load(data_path)
for i, (name, part_mesh) in enumerate(parts_mesh.geometry.items()):
    ...
```

So the prepared output should be a `trimesh.Scene` whose `geometry` dictionary contains one mesh per part.

### Available Libraries

The SAMPart3D `part` conda environment already has:

- `numpy`: available
- `trimesh`: available

It does not currently have:

- `pygltflib`
- `pymeshlab`

Phase 5 should use `trimesh` and avoid adding new dependencies.

### Canonical Mesh Choice

SAMPart3D was invoked with a staged GLB copied into the run directory:

```text
outputs/runs/<run>/sam/<run>.glb
```

The selected mask is copied to:

```text
outputs/runs/<run>/sam/mesh_1.0.npy
```

The bridge converter should prefer the staged GLB because it is the exact file passed to SAMPart3D and avoids filename/path issues with spaces. If the staged GLB is missing, the converter may fall back to `manifest.input_path`, but it must still validate face-count compatibility.

### Small Fragment Merge

Small part merging can be implemented with mesh topology:

1. Build an edge-to-face map from `mesh.faces`.
2. Any edge with two or more faces creates adjacency between those faces.
3. Count cross-label adjacency between each small part and non-small neighboring labels.
4. Merge each small part into the neighboring non-small label with the largest shared boundary count.
5. If no topological target exists, use centroid distance to the nearest non-small part.

All merge decisions should be recorded in `part_manifest.json`.

### Risks

- `trimesh.load(..., force="mesh")` flattens the GLB scene. This matches HoloPart's README bridge sample and is acceptable for Phase 5 because HoloPart samples geometry, not original materials.
- If the SAMPart3D mask was produced against a mesh that differs from the staged GLB's face order, face-count validation will fail. The converter should stop clearly rather than guessing.
- HoloPart `prepare_data` imports GPU-oriented dependencies. Phase 5 can validate `trimesh` scene load locally and should attempt HoloPart `prepare_data` through the HoloPart environment when available, but full inference remains Phase 6.

## Recommendation

Implement a `trimesh`-based bridge converter in PartPipeline, write bridge artifacts under `run_dir/bridge`, and integrate it into both:

- the normal single-run orchestrator after SAMPart3D success
- a dedicated command for converting an existing Phase 4 run without rerunning SAMPart3D

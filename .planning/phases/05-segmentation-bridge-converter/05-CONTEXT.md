# Phase 5 Context: Segmentation Bridge Converter

## Phase Goal

Convert a SAMPart3D face mask and source GLB into a HoloPart-compatible multipart GLB input.

## Locked Decisions

### Bridge Scope

Phase 5 stops at bridge conversion. It does not run full HoloPart completion.

The phase should produce a prepared multipart GLB from:

- the source GLB used for SAMPart3D
- the selected SAMPart3D face mask, defaulting to `mesh_1.0.npy`

The next phase, Phase 6, owns invoking HoloPart and collecting completed output.

### Small Part Handling

Small fragmented parts should be merged into neighboring parts by default.

The preferred first implementation is topology-based merging:

1. Count faces per part id.
2. Mark parts below the small-part threshold as small.
3. Build face adjacency from mesh topology, where adjacent faces share an edge.
4. For each small part, find the neighboring non-small part with the largest shared boundary.
5. Relabel the small part into that neighbor.
6. Record every merge in the part manifest.

If a small part has no valid topological neighbor, the implementation may fall back to nearest-part merging by spatial distance, but this fallback should be recorded in the manifest.

### Default Thresholds

Use configurable defaults rather than hardcoded constants:

```yaml
bridge:
  merge_small_parts: true
  min_faces_per_part: 100
  min_area_ratio: 0.001
```

The effective small-part rule should allow either absolute face count or area ratio to mark a part as small. Planning may refine exact threshold behavior if mesh area is easier to compute than expected.

### Output Artifacts

The bridge stage should write artifacts under the run directory, preferably under `bridge/`:

- `prepared_parts.glb`: multipart GLB prepared for HoloPart.
- `mesh_1.0_merged.npy`: relabeled mask after small-part merging.
- `part_manifest.json`: per-part statistics and merge history.
- optional visualization artifacts if cheap to generate.

The original SAMPart3D result must remain unchanged at `sam/mesh_1.0.npy`.

### Validation Expectations

The converter must validate face-count compatibility before writing final output.

The generated multipart GLB should be loadable by HoloPart `prepare_data`, but Phase 5 does not need to run full HoloPart inference.

## Open Technical Questions For Planning

- Which Python mesh library should be used for GLB read/write in the existing environment: `trimesh`, `pymeshlab`, Blender Python, or an existing HoloPart/SAMPart3D helper?
- Whether SAMPart3D mask labels correspond exactly to source mesh faces after its preprocessing, or whether the converter should use SAMPart3D's staged/rendered mesh as the canonical geometry.
- How to preserve materials and transforms when splitting the GLB into part geometries.
- Whether HoloPart `prepare_data` expects separate mesh nodes, separate geometry primitives, or a specific object naming convention.

## Out Of Scope

- Full HoloPart completion run.
- Batch conversion.
- Server execution.
- Presentation packaging beyond bridge-stage artifacts.

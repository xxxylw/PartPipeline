# Phase 5 Discussion Log: Segmentation Bridge Converter

## Summary

The user wants Phase 5 to bridge SAMPart3D output into HoloPart input. The key additional decision is that tiny fragmented SAMPart3D parts should not remain as separate parts by default; they should be merged into neighboring larger parts.

## Decisions

### Small Fragment Handling

User asked whether small fragmented parts can be merged into adjacent parts. Decision: yes, Phase 5 should include small-part merging as part of the bridge converter.

Chosen behavior:

- Merge small parts into neighboring parts.
- Prefer topology adjacency by shared mesh edges/boundaries.
- Use nearest-part fallback only when topology adjacency cannot find a valid larger neighbor.
- Record merge details in `part_manifest.json`.

### Phase Boundary

Phase 5 remains a bridge-conversion phase:

- Input: source GLB plus SAMPart3D `mesh_1.0.npy`.
- Output: HoloPart-compatible multipart GLB plus bridge metadata.
- HoloPart full inference remains Phase 6.

## Next Step

Run `$gsd-plan-phase 5` to produce an implementation plan for the converter.

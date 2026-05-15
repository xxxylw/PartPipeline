# State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-15)

**Core value:** A user can provide one `.glb` or a folder of `.glb` files and receive organized, presentation-ready segmented and completed part outputs.
**Current focus:** Phase 6 - HoloPart Integration

## Last Session

Completed Phase 5 segmentation bridge conversion. The real run at `outputs/runs/08.toulouse-20260515-160213` now has `bridge/prepared_parts.glb`, `bridge/mesh_1.0_merged.npy`, and `bridge/part_manifest.json`. The prepared GLB loads as 34 geometries and HoloPart `prepare_data(..., device="cpu")` succeeds. Next: invoke HoloPart on the prepared multipart GLB and collect the completed output.

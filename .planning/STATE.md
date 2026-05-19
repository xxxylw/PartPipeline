# State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-15)

**Core value:** A user can provide one `.glb` or a folder of `.glb` files and receive organized, presentation-ready segmented and completed part outputs.
**Current focus:** Phase 9 ready to execute - Exploded Assembly Presentation Video

## Last Session

Completed Phase 8 presentation packaging. PartPipeline now has `package` and `package-batch` commands that create presentation directories with Level A `bridge/prepared_parts.glb` as the default/recommended result and Level B `holopart/output.glb` as an explicit optional comparison artifact. A real smoke test packaged `outputs/runs/02.-01-20260518-190552` into `outputs/presentation/02.-01-20260518-190552`.

## Accumulated Context

### Roadmap Evolution

- Phase 8 added: Presentation Package and Output Levels.
- Phase 8 planned: Presentation package commands will produce `presentation_manifest.json` and `presentation_batch_manifest.json`, defaulting to Level A and requiring explicit opt-in for Level B and original GLB copying.
- Phase 8 complete: presentation packaging writes `level_a_segmented_parts.glb`, optional `level_b_holopart_output.glb`, `part_manifest.json`, and presentation manifests.
- Phase 9 added: Presentation Materials and Per-Part Exports, focused on turning the Level A package into richer review/reporting materials.
- Phase 9 refined: the key presentation deliverable should be an exploded-assembly animation/video where segmented Level A parts slide outward from the assembled model center and then slide back into place.
- Phase 9 planned: use `trimesh + matplotlib + OpenCV` to export part GLBs and render a real exploded/reassembled MP4 from Level A packages.

### Prior Verification Anchors

- Phase 7 real sample: `02.香叶天竺葵01.glb` completed the SAMPart3D -> bridge -> HoloPart batch path; its HoloPart output loaded as a `trimesh.Scene` with 5 geometries.
- Phase 8 smoke testing should use the existing Phase 7 run when available: `outputs/runs/02.-01-20260518-190552`.

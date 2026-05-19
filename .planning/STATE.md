# State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-15)

**Core value:** A user can provide one `.glb` or a folder of `.glb` files and receive organized, presentation-ready segmented and completed part outputs.
**Current focus:** Phase 8 - Presentation Package and Output Levels

## Last Session

Planned Phase 8 presentation packaging. The phase will add presentation package commands for single runs and batch manifests, with Level A `bridge/prepared_parts.glb` as the default/recommended output and Level B `holopart/output.glb` as an explicit optional comparison artifact. Planning artifacts are available in `.planning/phases/08-presentation-package-and-output-levels/08-RESEARCH.md` and `08-01-PLAN.md`.

## Accumulated Context

### Roadmap Evolution

- Phase 8 added: Presentation Package and Output Levels.
- Phase 8 planned: Presentation package commands will produce `presentation_manifest.json` and `presentation_batch_manifest.json`, defaulting to Level A and requiring explicit opt-in for Level B and original GLB copying.

### Prior Verification Anchors

- Phase 7 real sample: `02.香叶天竺葵01.glb` completed the SAMPart3D -> bridge -> HoloPart batch path; its HoloPart output loaded as a `trimesh.Scene` with 5 geometries.
- Phase 8 smoke testing should use the existing Phase 7 run when available: `outputs/runs/02.-01-20260518-190552`.

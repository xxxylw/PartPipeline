# State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-15)

**Core value:** A user can provide one `.glb` or a folder of `.glb` files and receive organized, presentation-ready segmented and completed part outputs.
**Current focus:** Phase 8 - Presentation Package and Output Levels

## Last Session

Completed Phase 7 batch runtime and real-model verification. PartPipeline can stage GLBs into `inputs/phase7`, run `batch` over a directory, write `batch_manifest.json`, and preserve per-run outputs. A real sample `02.香叶天竺葵01.glb` completed the SAMPart3D -> bridge -> HoloPart path with batch status `complete`; `holopart/output.glb` loaded as a `trimesh.Scene` with 5 geometries. New product decision for Phase 8: default presentation output should be Level A `bridge/prepared_parts.glb` because it preserves the original geometry more reliably; Level B `holopart/output.glb` remains optional comparison/enhancement because HoloPart can produce unstable or messy geometry.

## Accumulated Context

### Roadmap Evolution

- Phase 8 added: Presentation Package and Output Levels.

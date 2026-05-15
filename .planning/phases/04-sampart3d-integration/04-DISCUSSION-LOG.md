# Phase 4 Discussion Log

**Date:** 2026-05-15
**Phase:** SAMPart3D Integration

## User Decisions

### Real SAMPart3D Scope

Question: Should Phase 4 run full SAMPart3D or only wire a runner skeleton?

Decision: Full SAMPart3D run.

Rationale: Phase 4 should prove the real integration by running render, train, and eval, then locating `mesh_1.0.npy`.

### Output Organization

Question: Should PartPipeline copy key SAMPart3D results into its own run directory or only reference original SAMPart3D paths?

Decision: Copy/archive key selected results into the PartPipeline run directory and also record original SAMPart3D paths.

Rationale: The final pipeline needs presentation-ready organized outputs, while original paths remain useful for debugging.

### Missing Dependency Behavior

Question: Should Phase 4 auto-install/download missing dependencies, weights, or Blender?

Decision: No automatic mutation. Fail clearly with logs and hints.

Rationale: Existing conda/model environments are fragile. Phase 4 should be reproducible and avoid silently changing runtime state.

## Locked Summary

The selected decision set was `1,1,1`:

1. Complete SAMPart3D run.
2. Copy key result into PartPipeline artifacts while preserving original paths.
3. Fail clearly when prerequisites are missing; do not auto-install or auto-download.

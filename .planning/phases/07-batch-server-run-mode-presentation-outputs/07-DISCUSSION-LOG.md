# Phase 7: Batch, Server Run Mode, and Presentation Outputs - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-18
**Phase:** 7-Batch, Server Run Mode, and Presentation Outputs
**Areas discussed:** Phase scope, input sample, output depth, phase split

---

## Phase Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Discuss everything | Lock input paths, batch command, output structure, and server mode. | yes |
| Only discuss paths | Focus on GLB copy location, input manifest, and output root. | |
| Only discuss server | Focus on `d5` server run shape first. | |

**User's choice:** Discuss everything.
**Notes:** Phase 7 should lock all major runtime and path decisions before planning.

---

## Input Sample

| Option | Description | Selected |
|--------|-------------|----------|
| Small sample | Pick 2-3 GLBs from `gt_glbs` to validate the path and batch shape first. | yes |
| Full directory | Process all 8 GLBs immediately. | |
| User-specified files | User names exact files. | |

**User's choice:** Small sample.
**Notes:** Source directory is `C:\Users\qirui.huang\Downloads\assets\gt_glbs`; implementation should copy chosen GLBs into a PartPipeline-managed WSL path.

---

## Output Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Structured results | Preserve manifests, masks, prepared GLB, final GLB, and logs. | yes |
| Presentation package | Add a central presentation directory with copied final outputs and summary JSON. | |
| Maximum presentation materials | Add per-part exports and richer presentation artifacts in this same phase. | |

**User's choice:** User asked whether maximum presentation materials would be heavy.
**Notes:** Recommendation was to keep Phase 7 focused on stable batch production and defer per-part exports/richer presentation artifacts to Phase 8.

---

## Phase Split

| Option | Description | Selected |
|--------|-------------|----------|
| Keep all in Phase 7 | Batch, server, and per-part presentation exports together. | |
| Split into Phase 7 and Phase 8 | Phase 7 stabilizes batch/server basics; Phase 8 handles presentation package and per-part exports. | yes |

**User's choice:** Accepted the split.
**Notes:** Phase 7 = batch + path management + server-ready runtime + baseline structured outputs. Phase 8 = presentation package + per-part exports + richer visual/review materials.

---

## the agent's Discretion

- The agent may pick the initial 2-3 GLBs, prioritizing smaller files and one representative furniture-like asset if runtime allows.
- The agent may design the exact batch manifest schema.
- The agent may keep server execution documented/configured first, then leave full server validation for a later pass if local batch is not stable yet.

## Deferred Ideas

- Per-part exports.
- Central presentation package.
- Preview images or HTML report.

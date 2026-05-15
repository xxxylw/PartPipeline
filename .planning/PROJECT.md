# PartPipeline

## What This Is

PartPipeline is a WSL-based orchestration project for turning Trellis2-generated `.glb` assets into segmented and completed part outputs. It runs SAMPart3D for face-level part segmentation, converts the segmentation into HoloPart-compatible multipart GLB input, then runs HoloPart to generate complete part geometry.

## Core Value

A user can provide one `.glb` or a folder of `.glb` files and receive organized, presentation-ready segmented and completed part outputs.

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] Create `/home/rui/of_work/code/PartPipeline` as a standalone git project.
- [ ] Link forked SAMPart3D and HoloPart repositories as controllable dependencies.
- [ ] Support single-file and batch pipeline commands.
- [ ] Default SAMPart3D mask selection to `mesh_1.0.npy` for v1.
- [ ] Preserve complete outputs for presentation: masks, prepared multipart GLB, completed GLB, per-part exports where practical, logs, and manifest JSON.
- [ ] Prefer a shared runtime environment if feasible; otherwise use an environment dispatcher while keeping the user-facing command unified.

### Out of Scope

- Training new segmentation or completion models - PartPipeline orchestrates existing model projects.
- Committing model weights or generated outputs - these remain local artifacts.
- Building a web UI in v1 - presentation outputs can support a later UI/report phase.

## Context

Input assets currently live in `D:\of_work\resources\Disassembled parts` and include Trellis2-generated `.glb` files. Existing WSL projects live under `/home/rui/of_work/code`: SAMPart3D, HoloPart, and TRELLIS.2. SAMPart3D already outputs face-label arrays such as `results/5000/mesh_1.0.npy`; HoloPart expects a multipart `.glb` scene where each part is a separate geometry.

## Constraints

- **Runtime**: Work happens in WSL Ubuntu under `/home/rui/of_work/code` because the model projects and conda environments are there.
- **Dependencies**: SAMPart3D and HoloPart are heavy model repos; use submodules/forks instead of copying code.
- **Environment**: Investigate one shared conda environment, but accept dispatching to `p3sam` and `holopart` if dependency conflicts make a shared env fragile.
- **Default segmentation**: v1 uses SAMPart3D scale `1.0` unless the user overrides it.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Project name is PartPipeline | Clear and direct for the workflow | Pending |
| Project path is `/home/rui/of_work/code/PartPipeline` | Keeps it with related WSL code projects | Pending |
| SAMPart3D and HoloPart are linked through user forks | Allows local fixes while tracking upstream | Pending |
| Default SAMPart3D mask scale is `1.0` | Simple v1 behavior; scale selection can improve later | Pending |
| Support both `run` and `batch` commands | Covers single asset debugging and folder processing | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

After each phase transition:
1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. What This Is still accurate? Update if drifted.

After each milestone:
1. Full review of all sections.
2. Core Value check.
3. Audit Out of Scope.
4. Update Context with current state.

---
*Last updated: 2026-05-15 after initialization*

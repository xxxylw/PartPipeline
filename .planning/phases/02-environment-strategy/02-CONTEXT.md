# Phase 2 Context: Environment Strategy

## Domain

This phase decides how PartPipeline coordinates Python/conda environments for SAMPart3D and HoloPart. It does not run full model inference or install new dependency stacks.

## Decisions

- User-facing commands must stay unified through PartPipeline.
- Investigate whether a shared conda environment is feasible, but do not make shared-env success a blocker.
- Prefer stability over theoretical cleanliness: if shared dependencies look fragile, choose an environment dispatcher.
- Existing candidate environments are `part` for SAMPart3D and `holopart` for HoloPart.
- Phase 2 should use lightweight import/version checks, not full segmentation/completion runs.

## Code Context

- `configs/default.yaml` currently names `part` and `holopart` as the default environments.
- `third_party/SAMPart3D/tools/run_sampart3d_object.py` exists and will be used in Phase 3.
- `third_party/HoloPart/scripts/inference_holopart.py` exists and will be used in Phase 5.

## Canonical Refs

- `.planning/PROJECT.md` - project context and constraints.
- `.planning/REQUIREMENTS.md` - ENV-01 and ENV-02.
- `.planning/ROADMAP.md` - Phase 2 boundary.
- `configs/default.yaml` - current environment names.
- `third_party/SAMPart3D/requirements.txt` - SAMPart3D dependency requirements.
- `third_party/HoloPart/requirements.txt` - HoloPart dependency requirements.

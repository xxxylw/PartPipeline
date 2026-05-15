# Phase 4: SAMPart3D Integration - Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers the first real model integration in PartPipeline: a single `.glb` input can trigger SAMPart3D through the existing layered runner architecture, run render/train/eval, and locate the default `mesh_1.0.npy` segmentation result.

This phase is single-file only. It does not run HoloPart, does not convert masks into multipart GLB, does not implement batch processing, and does not run on the server.

</domain>

<decisions>
## Implementation Decisions

### SAMPart3D Execution Scope
- **D-01:** Phase 4 must run the complete SAMPart3D flow: render, train, and eval.
- **D-02:** The success target is a real SAMPart3D result file, defaulting to `mesh_1.0.npy` under the selected eval checkpoint result folder.
- **D-03:** The runner should use the existing SAMPart3D wrapper entrypoint: `third_party/SAMPart3D/tools/run_sampart3d_object.py`.

### Runtime Environment
- **D-04:** SAMPart3D runs with the `part` conda environment, not `p3sam`.
- **D-05:** The Phase 4 runner must manage the CUDA loader path issue through project-controlled runtime setup, such as a run-state symlink directory and `LD_LIBRARY_PATH`. It must not require the user to edit the conda environment manually.
- **D-06:** If Blender, SAMPart3D weights, or required runtime dependencies are missing, the command should fail clearly with logs and actionable hints. Phase 4 should not silently download weights, install packages, or mutate conda environments.

### Output and Manifest Behavior
- **D-07:** PartPipeline should copy or otherwise archive the key selected SAMPart3D result into the PartPipeline run directory, under the run's `sam/` area.
- **D-08:** The manifest should record both the PartPipeline-owned copied result path and the original SAMPart3D repo output paths.
- **D-09:** The manifest should record render, train, eval, result, and log paths. Failures should mark the manifest failed and include the failing step plus log paths.
- **D-10:** Mask scale defaults to `1.0`, and Phase 4 should preserve the existing CLI override behavior for future non-default scale selection.

### the agent's Discretion
- Choose the exact dataclass shape for SAMPart3D result metadata.
- Choose whether copying the selected `.npy` is implemented with `shutil.copy2` or a small artifact helper.
- Choose the most testable split between `orchestrator.py` and a new `runners/sampart3d.py`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope
- `.planning/ROADMAP.md` — Defines Phase 4 goal and success criteria.
- `.planning/REQUIREMENTS.md` — Defines `CLI-01`, `CLI-03`, and `BRIDGE-01`.
- `.planning/PROJECT.md` — Defines core value, default mask scale, and output expectations.

### Prior Phase Architecture
- `.planning/phases/03-runtime-configuration-layered-core/03-CONTEXT.md` — Captures layered runtime design decisions.
- `.planning/phases/03-runtime-configuration-layered-core/03-PLAN.md` — Defines CLI/config/orchestrator/runner/artifact boundaries.
- `.planning/phases/03-runtime-configuration-layered-core/03-VALIDATION.md` — Records current automated coverage and Phase 3 validation scope.
- `docs/runtime-core.md` — Explains runtime layers and artifact layout.

### Environment Strategy
- `docs/environment-strategy.md` — Current dispatcher decision: SAMPart3D uses `part`, HoloPart uses `holopart`.
- `.planning/phases/02-environment-strategy/02-SHARED-ENV-RECHECK.md` — Records shared-env recheck and CUDA loader symlink finding.

### SAMPart3D Entrypoint
- `third_party/SAMPart3D/tools/run_sampart3d_object.py` — Existing single-object wrapper that renders, trains, evaluates, and reports result directories.
- `third_party/SAMPart3D/configs/sampart3d/sampart3d-trainmlp-render16views.py` — Default config template used by the wrapper.
- `third_party/SAMPart3D/launch/train.py` — SAMPart3D training entrypoint called by the wrapper.
- `third_party/SAMPart3D/launch/eval.py` — SAMPart3D evaluation entrypoint called by the wrapper.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/partpipeline/cli.py`: already accepts `run`, `--profile`, `--output-dir`, `--mask-scale`, and `--dry-run`.
- `src/partpipeline/config.py`: already resolves `local_wsl` and `server` profiles and tool runtimes.
- `src/partpipeline/orchestrator.py`: currently creates the run manifest and records a placeholder SAMPart3D command.
- `src/partpipeline/runners/base.py`: provides the subprocess execution contract and log capture.
- `src/partpipeline/artifacts.py`: creates `logs/`, `sam/`, `prepared/`, `holopart/`, and writes `manifest.json`.
- `src/partpipeline/types.py`: contains dataclasses to extend with SAMPart3D result metadata if needed.

### Established Patterns
- CLI delegates downward; model execution must not live in `cli.py`.
- Runner code owns subprocess behavior; artifact code owns layout and manifest writing.
- Config/profile values should provide repo paths, Python paths, env names, output roots, and future server placeholders.
- Generated outputs stay under `outputs/` and are ignored by git.

### Integration Points
- Replace `_planned_sampart3d_command()` in `orchestrator.py` with a real SAMPart3D runner path for non-dry-run commands.
- Add a SAMPart3D-specific runner module, likely `src/partpipeline/runners/sampart3d.py`.
- Extend tests to cover command construction, CUDA loader environment construction, result discovery, manifest status, and failure behavior without requiring heavy model execution.

</code_context>

<specifics>
## Specific Ideas

- Use `/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb` as the likely manual verification GLB because Phase 3 dry-run already confirmed the path exists.
- Preserve mask scale `1.0` as the default selected result: `mesh_1.0.npy`.
- Prefer clear failure over implicit setup. If weights or Blender are missing, report that directly instead of downloading or installing.
- Preserve original SAMPart3D output paths in the manifest even when copying selected results into the PartPipeline run directory.

</specifics>

<deferred>
## Deferred Ideas

- Shared environment promotion remains deferred until a cloned shared-env spike passes both SAMPart3D and HoloPart gates.
- HoloPart execution is Phase 6.
- Mask-to-multipart GLB conversion is Phase 5.
- Batch processing and server execution are Phase 7.

</deferred>

---

*Phase: 04-SAMPart3D Integration*
*Context gathered: 2026-05-15*

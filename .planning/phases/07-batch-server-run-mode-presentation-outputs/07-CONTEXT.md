# Phase 7: Batch, Server Run Mode, and Presentation Outputs - Context

**Gathered:** 2026-05-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 turns the already-working single-asset pipeline into a managed batch workflow. It owns input path management, small-sample batch execution, a server-ready runtime shape, and baseline structured outputs. It does not own advanced presentation packaging or per-part exports; those are deferred to Phase 8 so this phase can keep the production path stable.

</domain>

<decisions>
## Implementation Decisions

### Input Path Management
- **D-01:** Source GLBs for Phase 7 may be selected from `C:\Users\qirui.huang\Downloads\assets\gt_glbs`.
- **D-02:** PartPipeline should copy selected GLBs into a project-managed WSL input directory before running, rather than depending on the Windows Downloads path at runtime.
- **D-03:** Recommended managed input directory: `/home/rui/of_work/code/PartPipeline/inputs/phase7/`.
- **D-04:** Manifests should preserve both the original source path and the managed runtime input path when practical, so later debugging can trace where a GLB came from.

### Batch Scope
- **D-05:** Use a small sample first: select 2-3 GLBs from `gt_glbs` to validate batch orchestration and path conventions.
- **D-06:** Keep the command capable of accepting a directory, so the same implementation can later process all 8 GLBs without changing the user-facing shape.
- **D-07:** Batch processing should create one independent run directory per asset and a batch-level manifest that indexes all runs.

### Pipeline Command Shape
- **D-08:** Phase 7 should connect the existing stages into a more complete command path: SAMPart3D -> bridge -> HoloPart.
- **D-09:** Existing step commands (`run`, `bridge`, `holopart`) should remain useful for debugging individual stages.
- **D-10:** The batch command should report per-asset success/failure and preserve enough paths to resume or inspect failed assets manually.

### Structured Outputs
- **D-11:** Phase 7 baseline output should be structurally complete rather than visually polished.
- **D-12:** Each asset run should preserve: `manifest.json`, selected SAM mask, `bridge/prepared_parts.glb`, `bridge/part_manifest.json`, `holopart/output.glb`, and `logs/`.
- **D-13:** Add or extend a batch-level manifest for aggregate status, asset list, run directories, failures, and timings where practical.

### Server-Ready Runtime
- **D-14:** Phase 7 should keep server concerns in the design: profile-based paths, predictable inputs/outputs, clear docs for host `d5`, and no hard dependency on Windows-only paths after input staging.
- **D-15:** Server execution can remain a documented/configured shape in this phase; full server validation can happen after the local batch path is stable.
- **D-16:** Continue using environment dispatch: SAMPart3D uses the `part` environment; HoloPart uses the `holopart` environment.

### the agent's Discretion
- The agent may choose the initial 2-3 GLBs, prioritizing smaller files and at least one realistic furniture-like asset if runtime allows.
- The agent may decide the exact batch manifest schema, as long as it is readable JSON and includes asset identity, input path, run directory, status, and error details.
- The agent may choose conservative defaults for continue-on-error behavior, but failures must be visible and inspectable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/PROJECT.md` - Defines PartPipeline purpose, constraints, and core value.
- `.planning/REQUIREMENTS.md` - Defines `CLI-02`, `OUT-01`, and `OUT-02` requirements relevant to Phase 7.
- `.planning/ROADMAP.md` - Defines Phase 7 goal and success criteria.
- `.planning/STATE.md` - Captures current project state after Phase 6.

### Prior Phase Contracts
- `.planning/phases/04-sampart3d-integration/04-SUMMARY.md` - Documents real SAMPart3D integration behavior and output expectations.
- `.planning/phases/05-segmentation-bridge-converter/05-SUMMARY.md` - Documents bridge output structure and prepared GLB behavior.
- `.planning/phases/06-holopart-integration/06-SUMMARY.md` - Documents HoloPart runner behavior and final output path.
- `.planning/phases/06-holopart-integration/06-VERIFICATION.md` - Documents the real successful HoloPart run and weight download caveat.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/partpipeline/cli.py` - Already has `run`, `bridge`, `holopart`, and a placeholder `batch` command.
- `src/partpipeline/orchestrator.py` - Already has `prepare_single_run`, `bridge_existing_run`, and `run_holopart_for_existing_run`.
- `src/partpipeline/artifacts.py` - Already creates per-run artifact directories and manifests.
- `src/partpipeline/types.py` - Already serializes SAMPart3D, bridge, and HoloPart result sections.
- `configs/default.yaml` - Already supports `local_wsl` and `server` profiles.

### Established Patterns
- Runtime work is organized around profiles and layered runners rather than ad hoc shell scripts.
- Generated outputs are local artifacts and should not be committed.
- Each model step records command, environment, cwd, exit code, and log paths.
- Existing commands should remain useful for stage-by-stage debugging.

### Integration Points
- Batch orchestration should call existing orchestrator functions instead of duplicating model invocation logic.
- Input staging should happen before run path creation so manifests can refer to stable WSL-side input files.
- Batch manifests should live under the selected output root, separate from per-asset `manifest.json` files.

</code_context>

<specifics>
## Specific Ideas

- User wants Phase 7 to discuss and lock input path handling, batch command behavior, output structure, and server mode.
- User provided source directory: `C:\Users\qirui.huang\Downloads\assets\gt_glbs`.
- User agreed to start with a small sample from `gt_glbs`.
- User initially wanted per-part exports and richer presentation materials, but accepted splitting heavier presentation work into a later phase.

</specifics>

<deferred>
## Deferred Ideas

- Phase 8 should handle richer presentation packaging.
- Phase 8 should handle per-part exports such as individual part `.glb` or `.ply` files.
- Phase 8 may include preview images, HTML reports, or other review-friendly display material.

</deferred>

---

*Phase: 7-Batch, Server Run Mode, and Presentation Outputs*
*Context gathered: 2026-05-18*

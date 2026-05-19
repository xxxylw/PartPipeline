# Phase 8: Presentation Package and Output Levels - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 packages already-generated PartPipeline outputs into presentation-ready directories. It defines output levels for display: Level A is the default segmented-parts result from `bridge/prepared_parts.glb`, while Level B is the optional HoloPart completion result from `holopart/output.glb`. This phase does not change SAMPart3D segmentation, bridge conversion, HoloPart inference, or batch execution.

</domain>

<decisions>
## Implementation Decisions

### Output Levels
- **D-01:** Level A is the default and recommended presentation result.
- **D-02:** Level A source is `bridge/prepared_parts.glb`.
- **D-03:** Level A should be named clearly in presentation output, for example `level_a_segmented_parts.glb`.
- **D-04:** Level B source is `holopart/output.glb`.
- **D-05:** Level B is an optional comparison/enhancement artifact, not the default display result, because HoloPart can produce unstable or messy geometry.
- **D-06:** Level B should only be copied when explicitly requested, for example with `--include-level-b`.

### Package Inputs
- **D-07:** Packaging should support a single completed run directory.
- **D-08:** Packaging should also support a batch manifest so a whole batch can be packaged into presentation directories.
- **D-09:** Batch packaging should read each item from `batch_manifest.json` and package items with usable per-run `manifest.json` paths.

### Original GLB Handling
- **D-10:** Original GLB copying should be optional, for example with `--include-original`.
- **D-11:** Even when original GLB is not copied, `presentation_manifest.json` should record the original/input path from the run manifest.

### Presentation Output Location
- **D-12:** The presentation root should be configurable with a CLI option, for example `--presentation-dir`.
- **D-13:** The default presentation root should be `outputs/presentation`.
- **D-14:** A single run package should be written under `outputs/presentation/<asset-or-run-name>/`.
- **D-15:** A batch package should create one child directory per packaged item and should include a batch-level presentation index if practical.

### Manifest Contract
- **D-16:** Each presentation directory should include `presentation_manifest.json`.
- **D-17:** The manifest should explicitly state `default_level: "A"`.
- **D-18:** The manifest should mark Level A as `recommended_for_display`.
- **D-19:** The manifest should include paths for Level A, optional Level B, optional original GLB, `part_manifest.json`, source run manifest, and notes explaining Level B is optional.

### Agent Discretion
- The agent may choose exact CLI command names, but preferred names are `package` for one run and `package-batch` for a batch manifest.
- The agent may choose a conservative package directory slug derived from the run directory name to avoid unsafe filesystem characters.
- The agent may decide whether batch-level presentation index is named `presentation_batch_manifest.json` or similar, as long as it is JSON and easy to inspect.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/PROJECT.md` - Defines PartPipeline purpose and output/presentation goals.
- `.planning/REQUIREMENTS.md` - Defines `OUT-02`, the requirement Phase 8 directly supports.
- `.planning/ROADMAP.md` - Defines Phase 8 goal and success criteria.
- `.planning/STATE.md` - Captures the Phase 7 completion state and Level A/Level B product decision.

### Prior Phase Contracts
- `.planning/phases/05-segmentation-bridge-converter/05-SUMMARY.md` - Documents `bridge/prepared_parts.glb` and `part_manifest.json`.
- `.planning/phases/06-holopart-integration/06-SUMMARY.md` - Documents `holopart/output.glb` location and HoloPart behavior.
- `.planning/phases/07-batch-server-run-mode-presentation-outputs/07-SUMMARY.md` - Documents batch runtime, input staging, and output structure.
- `.planning/phases/07-batch-server-run-mode-presentation-outputs/07-VERIFICATION.md` - Documents the real successful batch sample and output paths.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/partpipeline/cli.py` - Existing Typer CLI should receive packaging commands.
- `src/partpipeline/types.py` - Existing `RunManifest` and `BatchManifest` serialization patterns can guide presentation manifest dataclasses.
- `src/partpipeline/artifacts.py` - Existing artifact helper style can be extended with presentation directory helpers.
- `src/partpipeline/orchestrator.py` - Existing manifest-reading patterns for `bridge_existing_run`, `run_holopart_for_existing_run`, and `run_batch_pipeline` show how to resolve run paths.

### Established Patterns
- Generated outputs are local artifacts and should not be committed.
- JSON manifests use `ensure_ascii=False` and serialize paths as strings.
- CLI commands should print the key output path so the user can immediately inspect it.
- Model execution and output packaging should stay separate; packaging should not invoke SAMPart3D or HoloPart.

### Integration Points
- A new packaging module can read `run_dir/manifest.json`, copy Level A/Level B/original/part manifest, and write `presentation_manifest.json`.
- Batch packaging can read `outputs/runs/batches/*/batch_manifest.json` and call the single-run package logic for each item.
- Tests should use temporary fake run directories and fake GLB files, not real generated assets.

</code_context>

<specifics>
## Specific Ideas

- User observed that `bridge/prepared_parts.glb` often looks better in MeshLab than HoloPart output.
- User wants default presentation output adjusted to two levels.
- Level A should be the default because it preserves original geometry and is more stable.
- Level B should continue to exist as optional HoloPart comparison.
- Preferred decision set selected by user: `1,1,3,3`.

</specifics>

<deferred>
## Deferred Ideas

- Preview images and HTML reports can remain future work if they would slow down the Level A/Level B packaging baseline.
- Automatic quality scoring between Level A and Level B is future work.
- Re-running HoloPart with alternative settings to improve Level B quality is future work; Phase 8 only packages existing outputs.

</deferred>

---

*Phase: 8-Presentation Package and Output Levels*
*Context gathered: 2026-05-19*

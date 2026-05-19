# Phase 9: Exploded Assembly Presentation Video - Context

**Gathered:** 2026-05-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 9 turns an existing Phase 8 Level A presentation package into clearer demo material. It should use `level_a_segmented_parts.glb` as the source, export individual part GLBs when needed, and render an exploded-assembly MP4 where segmented parts move outward from the assembled model center with a slight rotation, pause for inspection, then return to their assembled positions. This phase must not rerun SAMPart3D, bridge conversion, or HoloPart.

</domain>

<decisions>
## Implementation Decisions

### Primary Output
- **D-01:** The primary deliverable is a real MP4 video, not only an HTML preview or static report.
- **D-02:** The MP4 should be written inside the presentation package, preferably under an `animation/` subdirectory.
- **D-03:** The package should also include animation metadata, for example `animation/animation_manifest.json`, with source package, source Level A GLB, part count, duration, frame count, and output paths.

### Animation Behavior
- **D-04:** The animation starts from the assembled state.
- **D-05:** Parts move outward from the assembled model center toward the surrounding space.
- **D-06:** Parts should have a slight rotation while moving outward so the result feels more like a presentation and less like a raw technical transform.
- **D-07:** The animation should pause or linger briefly in the exploded state so the segmentation is easy to inspect.
- **D-08:** Parts then move back to their original assembled positions.
- **D-09:** The assembled final frame should match the original Level A arrangement.

### Camera And Framing
- **D-10:** Use a fixed three-quarter view by default.
- **D-11:** Avoid camera orbit for the initial implementation; the motion should come from the parts, not from moving the camera.
- **D-12:** The model should be framed so all parts remain visible at the exploded extent.

### Part Assets
- **D-13:** Export individual part files such as `parts/part_001.glb`, `parts/part_002.glb`, etc.
- **D-14:** The per-part exports should be based on the segmented geometries from Level A, not HoloPart Level B.
- **D-15:** The part export metadata should preserve stable part order and paths so the animation can be inspected or reused later.

### Batch Behavior
- **D-16:** Batch animation generation should be optional.
- **D-17:** Single-package animation generation is the default Phase 9 path to get right first.
- **D-18:** Batch presentation packaging may expose an option that generates animation/video for each item; when disabled, batch should not spend time rendering videos.
- **D-19:** Batch-level manifests should record animation paths for items where animation generation was requested and succeeded.

### Agent Discretion
- The agent may choose the exact CLI names, but the expected shape is a command for one package and an optional flag for batch animation generation.
- The agent may choose the rendering backend after research. Good candidates include Blender CLI, Python/trimesh-based frame generation plus ffmpeg, or another reliable local renderer.
- The agent may choose exact duration, FPS, easing curve, and rotation angle, as long as the motion visibly communicates exploded segmentation and produces a usable MP4.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning
- `.planning/PROJECT.md` - Defines the PartPipeline presentation-ready output goal.
- `.planning/REQUIREMENTS.md` - Defines `OUT-02` and `V2-PRESENTATION-REPORT`.
- `.planning/ROADMAP.md` - Defines Phase 9 goal and success criteria.
- `.planning/STATE.md` - Records Phase 8 completion and Phase 9 animation intent.

### Prior Phase Contracts
- `.planning/phases/05-segmentation-bridge-converter/05-SUMMARY.md` - Documents Level A source geometry as `bridge/prepared_parts.glb`.
- `.planning/phases/08-presentation-package-and-output-levels/08-SUMMARY.md` - Documents `level_a_segmented_parts.glb`, presentation package layout, and Level A/Level B semantics.
- `.planning/phases/08-presentation-package-and-output-levels/08-VERIFICATION.md` - Documents the real Phase 8 smoke package and output paths.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/partpipeline/presentation.py` - Existing presentation packaging logic should be extended or composed with animation generation.
- `src/partpipeline/types.py` - Existing manifest dataclass pattern should guide animation/part export metadata.
- `src/partpipeline/artifacts.py` - Existing JSON writer and directory helper style should guide new animation output helpers.
- `src/partpipeline/cli.py` - Existing Typer commands `package` and `package-batch` are the natural integration points.

### Established Patterns
- Generated assets live under `outputs/` and are ignored by git.
- Presentation commands read existing artifacts and write organized outputs; they do not run model inference.
- JSON manifests serialize paths as strings with `ensure_ascii=False`.
- Tests should use fake GLBs or temporary files unless a final smoke test uses the existing real Phase 8 package.

### Integration Points
- Single-package command can read `presentation_manifest.json` and `level_a_segmented_parts.glb`.
- Batch command can optionally call the single-package animation path per item.
- Animation outputs should be referenced from presentation manifests or batch presentation manifests so downstream demo tooling can find them.

</code_context>

<specifics>
## Specific Ideas

- User wants a component/part animation that starts assembled, slides outward from the center to the surrounding space, and slides back into the assembled position.
- User wants the motion to include slight rotation while moving outward for a more presentable effect.
- User wants a fixed three-quarter view.
- User wants individual part GLBs exported as `parts/part_001.glb`, etc.
- User wants batch animation generation supported as an option rather than always-on.
- The existing real package path to use for smoke testing is likely `outputs/presentation/02.-01-20260518-190552`.

</specifics>

<deferred>
## Deferred Ideas

- Interactive web viewer controls can be future work unless they are needed to generate or inspect the MP4.
- Camera orbit can be future work; fixed three-quarter view is preferred for Phase 9.
- Advanced lighting/material styling can be future work if it slows down the first reliable MP4 export.
- Automatic quality scoring between Level A and Level B remains out of scope.

</deferred>

---

*Phase: 9-Exploded Assembly Presentation Video*
*Context gathered: 2026-05-19*


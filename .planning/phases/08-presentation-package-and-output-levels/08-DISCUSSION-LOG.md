# Phase 8: Presentation Package and Output Levels - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-19
**Phase:** 8-Presentation Package and Output Levels
**Areas discussed:** Output levels, package inputs, original GLB handling, presentation output location

---

## Output Levels

| Option | Description | Selected |
|--------|-------------|----------|
| Level B explicit only | Default package includes Level A; HoloPart Level B is copied only with an explicit option. | yes |
| Include Level B if present | Automatically copy HoloPart output when it exists, but mark it as not recommended by default. | |
| Level A only | Do not handle Level B in this phase. | |

**User's choice:** Level B explicit only.
**Notes:** HoloPart currently produces unstable or messy geometry, so Level A should be the default presentation output.

---

## Package Inputs

| Option | Description | Selected |
|--------|-------------|----------|
| Single run and batch manifest | Support packaging one run and packaging all usable runs from a batch manifest. | yes |
| Single run only | Keep the first version limited to one run directory. | |
| Batch manifest only | Build only batch-level packaging. | |

**User's choice:** Single run and batch manifest.
**Notes:** This fits Phase 7, where both per-run manifests and batch manifests now exist.

---

## Original GLB Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Always copy original | Include `original.glb` in every package for visual comparison. | |
| Never copy original | Only record original path in manifest to save space. | |
| Optional original | Copy original only with an explicit option such as `--include-original`. | yes |

**User's choice:** Optional original.
**Notes:** This avoids bloating presentation packages by default while still allowing comparison when needed.

---

## Presentation Output Location

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed root | Always write to `outputs/presentation/<asset>/`. | |
| Inside run dir | Write to `<run_dir>/presentation/`. | |
| Configurable root | Use `--presentation-dir`, defaulting to `outputs/presentation`. | yes |

**User's choice:** Configurable root.
**Notes:** Default should be easy to find, but CLI should allow a custom destination for demos or sharing.

---

## Agent Discretion

- The agent may choose exact CLI command names, with `package` and `package-batch` preferred.
- The agent may design the exact presentation manifest schema, as long as it clearly marks Level A as default/recommended and Level B as optional.
- The agent may decide safe directory naming for presentation package folders.

## Deferred Ideas

- Preview images.
- HTML report.
- Automatic quality scoring for choosing between Level A and Level B.
- HoloPart tuning or reruns to improve Level B quality.

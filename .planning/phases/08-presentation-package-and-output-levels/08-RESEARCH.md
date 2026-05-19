---
phase: 8
type: research
status: complete
created: 2026-05-19
---

# Phase 8 Research: Presentation Package and Output Levels

## Goal

Phase 8 should package existing run artifacts into presentation-ready directories. It should not run SAMPart3D, bridge conversion, or HoloPart. The package contract should make Level A (`bridge/prepared_parts.glb`) the default/recommended display artifact and make Level B (`holopart/output.glb`) an explicit optional comparison artifact.

## Existing Code Fit

### CLI Layer

`src/partpipeline/cli.py` already exposes Typer commands for `stage-inputs`, `run`, `bridge`, `holopart`, and `batch`. Phase 8 should add two commands here:

- `package <run_dir>` for one completed run.
- `package-batch <batch_manifest>` for a batch manifest.

Both commands should print the resulting presentation path and manifest path, following the existing CLI output style.

### Types Layer

`src/partpipeline/types.py` contains dataclasses with `to_dict()` methods for run, bridge, HoloPart, input, and batch manifests. Phase 8 should add presentation-specific dataclasses rather than using loose dictionaries everywhere:

- `PresentationLevel` for Level A / Level B artifacts.
- `PresentationPackageManifest` for a single run package.
- `PresentationBatchItem` and `PresentationBatchManifest` for batch packaging.

Paths should serialize as strings, matching the existing manifest convention.

### Artifact Layer

`src/partpipeline/artifacts.py` already owns output directory helpers and JSON manifest writers. Phase 8 can add:

- a safe slug helper or public wrapper for presentation directory names
- `write_presentation_manifest(...)`
- `write_presentation_batch_manifest(...)`

The existing private `_safe_stem()` is useful but only accepts a `Path`. If reused, keep the API conservative or add a new small helper instead of broad refactoring.

### Orchestration Layer

`src/partpipeline/orchestrator.py` reads `manifest.json` and `batch_manifest.json` with `json.loads`. Presentation packaging is separate from model orchestration, so the cleanest shape is a new module:

- `src/partpipeline/presentation.py`

This keeps Phase 8 packaging logic out of the model execution orchestrator and preserves the layered design from Phase 3.

### Tests

Existing tests use `tempfile.TemporaryDirectory`, fake manifests, fake GLB bytes, and `CliRunner`. Phase 8 tests should follow the same pattern:

- Unit tests for single-run packaging with fake `bridge/prepared_parts.glb`, `bridge/part_manifest.json`, optional `holopart/output.glb`, and optional original GLB.
- Unit tests for batch packaging with fake `batch_manifest.json` containing one successful item and one failed item.
- CLI tests for `package` and `package-batch`.

No real SAMPart3D or HoloPart execution is needed.

## Recommended Implementation Shape

Create `src/partpipeline/presentation.py` with functions:

```python
def package_run(
    run_dir: Path,
    presentation_dir: Path = Path("outputs/presentation"),
    include_level_b: bool = False,
    include_original: bool = False,
) -> PresentationPackageManifest:
    ...

def package_batch(
    batch_manifest_path: Path,
    presentation_dir: Path = Path("outputs/presentation"),
    include_level_b: bool = False,
    include_original: bool = False,
) -> PresentationBatchManifest:
    ...
```

`package_run` should:

1. Read `<run_dir>/manifest.json`.
2. Resolve Level A from `manifest["bridge"]["prepared_glb"]`, falling back to `<run_dir>/bridge/prepared_parts.glb`.
3. Require Level A to exist.
4. Copy Level A to `<presentation_root>/<slug>/level_a_segmented_parts.glb`.
5. Copy `part_manifest.json` when it exists.
6. Copy Level B only when `include_level_b=True`; if requested but missing, fail clearly.
7. Copy original GLB only when `include_original=True`; if missing, fail clearly.
8. Always record the original/input path in `presentation_manifest.json`, even when not copied.
9. Mark `default_level` as `"A"` and Level A as `recommended_for_display`.

`package_batch` should:

1. Read `batch_manifest.json`.
2. Iterate items with non-empty `manifest_path` values.
3. Package only usable runs where the per-run manifest exists and Level A exists.
4. Continue through item-level packaging failures and record them in the batch presentation manifest.
5. Write a batch-level `presentation_batch_manifest.json`.

## Risks and Controls

- **Accidental model execution:** Keep packaging functions independent from `prepare_single_run`, `bridge_existing_run`, and `run_holopart_for_existing_run`.
- **Missing or messy HoloPart output:** Copy Level B only when explicitly requested and record it as optional comparison, not recommended output.
- **Large package size:** Do not copy original GLB unless `--include-original` is provided.
- **Ambiguous package selection:** Always emit `presentation_manifest.json` with clear `default_level`, `recommended_for_display`, and source paths.
- **Path collision:** Use a stable safe slug based on run directory name; if a package directory already exists, overwrite only the known generated filenames in that directory.

## Verification Strategy

Run targeted tests first:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest tests.test_presentation tests.test_cli
```

Then run the full existing suite:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover tests
```

Manual smoke test should package the real Phase 7 run:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli package outputs/runs/02.-01-20260518-190552
```

Expected output:

- `outputs/presentation/02.-01-20260518-190552/level_a_segmented_parts.glb`
- `outputs/presentation/02.-01-20260518-190552/presentation_manifest.json`


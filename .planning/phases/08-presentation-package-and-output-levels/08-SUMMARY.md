# Phase 8 Summary: Presentation Package and Output Levels

## Status

Complete.

## What Changed

Phase 8 added presentation packaging for already-generated PartPipeline outputs. The new packaging path does not run SAMPart3D, bridge conversion, or HoloPart; it only reads existing manifests, copies selected artifacts, and writes presentation manifests.

Implemented:

- `src/partpipeline/presentation.py`
- presentation manifest dataclasses in `src/partpipeline/types.py`
- presentation manifest writers and package directory helper in `src/partpipeline/artifacts.py`
- `partpipeline package <run_dir>`
- `partpipeline package-batch <batch_manifest>`
- `tests/test_presentation.py`
- CLI tests for single-run and batch presentation packaging

## Output Levels

Level A is now the default and recommended display output:

```text
bridge/prepared_parts.glb -> level_a_segmented_parts.glb
```

Level B remains available as an optional HoloPart comparison artifact:

```text
holopart/output.glb -> level_b_holopart_output.glb
```

Level B is copied only when the user passes `--include-level-b`. Original GLB copying is also opt-in with `--include-original`; the original input path is always recorded in `presentation_manifest.json`.

## Commands

Package one completed run:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli package outputs/runs/02.-01-20260518-190552
```

Package a batch manifest:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli package-batch outputs/runs/batches/<batch-id>/batch_manifest.json
```

Useful options:

```text
--presentation-dir outputs/presentation
--include-level-b
--include-original
```

## Real Smoke Result

Validated against the existing Phase 7 run:

```text
outputs/runs/02.-01-20260518-190552
```

Generated:

```text
outputs/presentation/02.-01-20260518-190552/level_a_segmented_parts.glb
outputs/presentation/02.-01-20260518-190552/part_manifest.json
outputs/presentation/02.-01-20260518-190552/presentation_manifest.json
outputs/presentation/presentation_batch_manifest.json
```

The Level A GLB is 14 MB and should be directly openable in MeshLab.

## Next Phase Readiness

The project now has a presentation-friendly default output level. Future work can add preview images, HTML reports, per-part exports, or quality scoring without changing the Level A/Level B contract.

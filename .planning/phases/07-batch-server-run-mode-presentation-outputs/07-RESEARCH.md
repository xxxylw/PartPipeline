# Phase 7 Research: Batch, Server Run Mode, and Presentation Outputs

## Research Goal

Answer what is needed to plan Phase 7 well: how to turn the existing single-asset pipeline into a managed batch workflow with stable input paths, batch manifests, server-ready configuration, and baseline structured outputs.

## Current Implementation Shape

### Existing Runtime Layers

PartPipeline already has the right layered shape for Phase 7:

- `src/partpipeline/cli.py`
  - `run` exists and currently runs SAMPart3D plus bridge conversion.
  - `bridge` exists for re-running conversion on an existing SAMPart3D run.
  - `holopart` exists for running HoloPart on an existing bridge output.
  - `batch` exists only as an inspection/count placeholder.
- `src/partpipeline/orchestrator.py`
  - `prepare_single_run(...)` performs single GLB processing through SAMPart3D and bridge, returning status `bridge_complete`.
  - `run_holopart_for_existing_run(...)` completes an existing bridge run and updates the same `manifest.json` to `holopart_complete`.
- `src/partpipeline/artifacts.py`
  - `create_run_paths(...)` creates stable per-run directories.
  - `write_manifest(...)` serializes `RunManifest`.
- `src/partpipeline/types.py`
  - Contains result dataclasses for SAMPart3D, bridge, and HoloPart.
  - Does not yet contain batch-level dataclasses.
- `configs/default.yaml`
  - Defines `local_wsl` and `server` profiles.
  - Runtime strategy is already dispatcher-based: SAMPart3D uses `part`, HoloPart uses `holopart`.

### Existing Output Contract

Each individual run already has the directories Phase 7 needs:

```text
run_dir/
  manifest.json
  logs/
  sam/
  bridge/
  prepared/
  holopart/
```

Phase 7 should not replace this structure. It should add a batch-level wrapper that indexes multiple existing per-run manifests.

## Input Path Management Findings

The user-provided Windows source is:

```text
C:\Users\qirui.huang\Downloads\assets\gt_glbs
```

When accessed from WSL, this maps to:

```text
/mnt/c/Users/qirui.huang/Downloads/assets/gt_glbs
```

Files currently available, ordered by size:

```text
10.蔷薇.glb                       4.8 MB
07.高粱03.glb                     7.5 MB
05.发财树05.glb                   12.0 MB
02.香叶天竺葵01.glb               13.0 MB
06.Loafer SC23 单人沙发.glb       51.1 MB
04.紫花风铃木 02.glb              64.6 MB
08.Toulouse 双人沙发组合.glb      87.9 MB
03.一球悬铃木 07.glb              123.4 MB
```

Recommended Phase 7 sample:

1. `10.蔷薇.glb` - smallest, good for fast path validation.
2. `07.高粱03.glb` - second-smallest, useful for batch count/status validation.
3. `06.Loafer SC23 单人沙发.glb` - furniture-like asset and path contains spaces/ASCII mix; useful for path robustness if runtime budget allows.

Managed WSL input directory should be:

```text
/home/rui/of_work/code/PartPipeline/inputs/phase7/
```

Generated staged inputs should not be committed. If not already ignored, `inputs/` should be ignored like `outputs/`.

## Batch Manifest Design

Add a batch-level manifest in the selected output root, for example:

```text
outputs/runs/batches/batch-20260518-183000/batch_manifest.json
```

Suggested schema:

```json
{
  "batch_id": "batch-20260518-183000",
  "profile": "local_wsl",
  "input_dir": "/home/rui/of_work/code/PartPipeline/inputs/phase7",
  "output_root": "/home/rui/of_work/code/PartPipeline/outputs/runs",
  "mask_scale": "1.0",
  "status": "complete",
  "created_at": "2026-05-18T18:30:00",
  "updated_at": "2026-05-18T18:45:00",
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "items": [
    {
      "asset_name": "10.蔷薇.glb",
      "input_path": "/home/rui/of_work/code/PartPipeline/inputs/phase7/10.蔷薇.glb",
      "source_path": "/mnt/c/Users/qirui.huang/Downloads/assets/gt_glbs/10.蔷薇.glb",
      "run_dir": "...",
      "manifest_path": ".../manifest.json",
      "status": "holopart_complete",
      "error": null
    }
  ]
}
```

Status rules:

- `complete`: all assets completed HoloPart.
- `partial`: at least one asset failed and at least one succeeded.
- `failed`: all attempted assets failed.
- `dry_run`: dry-run only, commands inspected but no model execution.
- `empty`: no GLBs found.

Continue-on-error should be the conservative default for batch: one failed asset should not hide the status of other assets. Failures must be recorded clearly.

## Batch Orchestration Design

Recommended orchestration function:

```python
run_batch_pipeline(
    input_dir: Path,
    config_path: Path,
    profile_name: str | None = None,
    output_dir: Path | None = None,
    mask_scale: str | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    continue_on_error: bool = True,
    run_holopart: bool = True,
) -> BatchManifest
```

For each `.glb`:

1. Call `prepare_single_run(...)`.
2. If not dry-run and `run_holopart=True`, call `run_holopart_for_existing_run(...)` on the returned run directory.
3. Record item status, run directory, manifest path, and error details.
4. Write/update `batch_manifest.json` after each item so interrupted batches remain inspectable.

Dry-run should avoid real model execution and use existing `prepare_single_run(... dry_run=True)`. It should still create a batch manifest so tests and users can inspect exactly what would run.

## CLI Design

Replace the current placeholder `batch` command with real orchestration:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli batch inputs/phase7
```

Useful options:

```text
--output-dir / -o
--config / -c
--profile / -p
--mask-scale
--dry-run
--limit
--stop-on-error
--skip-holopart
```

Input staging can be implemented as either a separate helper command or an option. For Phase 7, a simple separate command keeps responsibilities clearer:

```bash
partpipeline stage-inputs /mnt/c/Users/qirui.huang/Downloads/assets/gt_glbs \
  --destination inputs/phase7 \
  --limit 3
```

The staging command should copy `.glb` files and write `inputs/phase7/input_manifest.json` with original and staged paths.

## Server-Ready Runtime Findings

Server profile currently records:

```text
Host alias: d5
HostName: 10.1.6.8
User: qzqd5
Port: 19091
```

Phase 7 should not hardcode Windows paths into runtime manifests after staging. Server documentation should show the equivalent flow:

1. Put inputs under a project-managed directory on the server, for example:

```text
/server/path/placeholder/PartPipeline/inputs/phase7/
```

2. Run the same CLI using the `server` profile once server placeholder paths are filled:

```bash
PYTHONPATH=src /server/path/placeholder/miniconda3/envs/part/bin/python \
  -m partpipeline.cli batch inputs/phase7 --profile server
```

3. Keep generated outputs under:

```text
outputs/server-runs/
```

Full server validation can be deferred until local batch is stable.

## Testing Strategy

Unit tests should avoid real model execution:

- Test input staging copies selected `.glb` files and records `input_manifest.json`.
- Test batch dry-run creates a batch manifest with the expected item count.
- Test batch orchestration with fake runners records success and failure items.
- Test CLI prints batch status, batch manifest path, and per-item counts.
- Test path names with spaces/non-ASCII survive staging and manifest serialization.

Real verification should run in two levels:

1. Fast verification:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
```

2. Phase 7 sample verification:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli stage-inputs \
  /mnt/c/Users/qirui.huang/Downloads/assets/gt_glbs \
  --destination inputs/phase7 \
  --limit 3

PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli batch \
  inputs/phase7 \
  --limit 2
```

If full model execution takes too long or fails on a sample asset, Phase 7 can still record a clear blocker in `07-VERIFICATION.md`, but it should not mark CLI-02 complete unless at least dry-run batch and one real item path are proven.

## Risks And Mitigations

| Risk | Mitigation |
|------|------------|
| Batch run takes a very long time | Implement `--limit`; validate with 2-3 samples first. |
| One asset failure stops all progress | Default to continue-on-error and record item errors. |
| Windows paths leak into server runtime | Stage inputs into project-managed WSL/server directories before processing. |
| HoloPart weight/download issue repeats | Reuse Phase 6 local weights and document server weight placement. |
| Batch manifest becomes detached from per-run manifests | Store run_dir and manifest_path for each item and update batch manifest after each asset. |
| Unicode/spaces in filenames break shell paths | Use Python `Path` and subprocess argument lists; test with filenames containing spaces and Chinese characters. |

## Recommendation

Plan Phase 7 as one implementation plan with five tasks:

1. Add input staging and input manifest support.
2. Add batch manifest/result dataclasses and artifact helpers.
3. Implement batch orchestration with continue-on-error and dry-run support.
4. Replace CLI batch placeholder and add `stage-inputs`.
5. Add server run documentation and Phase 7 verification using small staged samples.

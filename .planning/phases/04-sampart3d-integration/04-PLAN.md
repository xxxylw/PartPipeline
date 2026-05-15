---
phase: 4
phase_name: SAMPart3D Integration
status: planned
wave: 1
requirements_addressed:
  - CLI-01
  - CLI-03
  - BRIDGE-01
files_modified:
  - configs/default.yaml
  - src/partpipeline/types.py
  - src/partpipeline/orchestrator.py
  - src/partpipeline/runners/sampart3d.py
  - src/partpipeline/runners/__init__.py
  - src/partpipeline/artifacts.py
  - tests/test_sampart3d_runner.py
  - tests/test_orchestrator.py
  - tests/test_cli.py
  - docs/sampart3d-integration.md
---

# Phase 4 Plan: SAMPart3D Integration

## Objective

Run SAMPart3D for a single input `.glb` through PartPipeline's layered runner and locate the selected segmentation result, defaulting to `mesh_1.0.npy`.

The user-facing command remains one PartPipeline command. Internally, SAMPart3D runs through the `part` conda environment and the existing `third_party/SAMPart3D/tools/run_sampart3d_object.py` wrapper.

## Locked Decisions

- Run the complete SAMPart3D flow: render, train, eval.
- Use `part` for SAMPart3D.
- Copy/archive the selected `mesh_<scale>.npy` into the PartPipeline run directory under `sam/`.
- Also record original SAMPart3D output paths in `manifest.json`.
- Do not auto-install packages, download weights, download Blender, or mutate conda environments.
- Fail clearly when prerequisites are missing.

## Non-Goals

- Do not run HoloPart.
- Do not convert masks into multipart GLB.
- Do not implement batch execution.
- Do not inspect or execute on server `d5`.
- Do not solve shared environment promotion.

## Wave 1: Runner Contract and Preflight

### Task 1: Add SAMPart3D domain result types

Extend `src/partpipeline/types.py` with lightweight dataclasses for SAMPart3D metadata, such as:

- `Sampart3DPaths`
- `Sampart3DResult`
- optional `PreflightResult` / `PreflightIssue`

The structure should serialize cleanly into `manifest.json`.

Acceptance criteria:

- Types contain no subprocess logic.
- Result metadata can represent original SAMPart3D paths and copied PartPipeline artifact paths.
- Existing manifest serialization tests still pass.

### Task 2: Implement SAMPart3D runner module

Create `src/partpipeline/runners/sampart3d.py`.

Responsibilities:

- Build the command for `tools/run_sampart3d_object.py`.
- Use profile values for repo path, Python executable, and env name.
- Include `--glb`, `--exp-name`, `--weight-name`, `--backbone-weight`, `--blender`, and `--config-template` where appropriate.
- Build expected original output paths:
  - `mesh_root/<object>.glb`
  - `data_root/<object>`
  - `exp/sampart3d/<exp-name>/config.py`
  - `exp/sampart3d/<exp-name>/results/<weight-name>`
  - `exp/sampart3d/<exp-name>/results/<weight-name>/mesh_<mask-scale>.npy`
  - `exp/sampart3d/<exp-name>/vis_pcd/<weight-name>`
- Build a project-local CUDA loader directory under `outputs/run_state/part_cuda_lib/`.
- Create symlinks for stable CUDA library names where source libraries exist.
- Produce an `LD_LIBRARY_PATH` override containing the symlink directory and torch lib directory.

Acceptance criteria:

- Unit tests verify command construction without running SAMPart3D.
- Unit tests verify CUDA symlink planning/creation using temporary fake torch libraries.
- Unit tests verify expected `mesh_1.0.npy` path.
- Dry-run records the command and environment without executing.

### Task 3: Add preflight checks

The runner should check, before real execution:

- input `.glb` exists
- SAMPart3D repo exists
- wrapper script exists
- config template exists
- `part` Python executable exists
- Blender executable exists
- backbone weight exists
- CUDA symlink source libraries can be located

Failure behavior:

- Do not start the subprocess when preflight fails.
- Raise a typed error or return a structured failure that the orchestrator can write into the manifest.
- Error text should name the missing prerequisite and the path checked.

Acceptance criteria:

- Tests cover missing Blender and missing backbone weight.
- Tests assert no subprocess is invoked on preflight failure.
- Error messages are actionable.

## Wave 2: Orchestrator and Artifact Integration

### Task 4: Wire non-dry-run orchestration to SAMPart3D runner

Update `src/partpipeline/orchestrator.py`:

- Preserve existing dry-run behavior.
- For non-dry-run, call `Sampart3DRunner`.
- On success:
  - copy selected `mesh_<scale>.npy` into `paths.sam_dir`
  - write manifest status `sampart3d_complete`
  - include command result and SAMPart3D metadata
- On failure:
  - write manifest status `failed`
  - include failing step, command/log paths, and error details
  - re-raise or return a CLI-visible failure so the command exits non-zero

Acceptance criteria:

- Tests use a fake runner/result and do not run models.
- Tests verify successful manifest fields.
- Tests verify failed manifest status and log/error recording.

### Task 5: Extend artifact helpers for selected mask copying

Add a small helper in `src/partpipeline/artifacts.py` if needed:

- copy selected SAMPart3D mask into `sam/`
- preserve original filename or normalize to `mesh_<scale>.npy`
- return copied path

Acceptance criteria:

- Tests verify copying preserves contents and path in manifest.
- Missing source mask is a clear error.

### Task 6: Keep CLI behavior clean

Update `src/partpipeline/cli.py` only if needed for failure handling.

The CLI should:

- continue accepting `--dry-run`
- continue accepting `--mask-scale`
- print run directory and manifest path
- surface failures with a concise message and non-zero exit code

Acceptance criteria:

- CLI tests cover dry-run.
- CLI test with a fake/preflight failure verifies non-zero exit and manifest creation if feasible.

## Wave 3: Documentation and Verification

### Task 7: Document SAMPart3D integration

Create `docs/sampart3d-integration.md` describing:

- command flow
- required local prerequisites
- `part` environment
- CUDA loader symlink strategy
- expected SAMPart3D original paths
- PartPipeline artifact paths
- failure behavior

Acceptance criteria:

- Document explicitly says Phase 4 does not run HoloPart.
- Document tells user how to interpret missing Blender/weight failures.

### Task 8: Automated verification

Run:

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
/home/rui/miniconda3/envs/part/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli --help
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb" --dry-run
```

Expected result:

- Tests pass.
- CLI help works.
- Dry-run records a SAMPart3D command using `part`.
- No model subprocess runs during automated tests.

### Task 9: Manual real-run verification

Run only after preflight prerequisites are present:

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb"
```

Expected success result:

- SAMPart3D render/train/eval runs.
- The original result exists:
  - `third_party/SAMPart3D/exp/sampart3d/<exp-name>/results/5000/mesh_1.0.npy`
- The selected result is copied into:
  - `outputs/runs/<run>/sam/mesh_1.0.npy`
- `manifest.json` records:
  - profile
  - mask scale
  - command argv
  - stdout/stderr logs
  - render/train/eval/result paths
  - copied selected mask path
  - status `sampart3d_complete`

Expected missing-prerequisite result:

- CLI exits non-zero.
- `manifest.json` exists when the run directory has been created.
- Manifest status is `failed`.
- Error text identifies missing Blender, missing weight, missing CUDA source library, or other prerequisite.
- No dependency is installed and no resource is downloaded automatically.

## Plan Quality Checks

- Goal-backward: every Phase 4 success criterion maps to a task and verification step.
- Risk isolation: heavy model execution is excluded from unit tests and kept as manual verification.
- Architecture: CLI remains thin; runner owns SAMPart3D subprocess behavior; artifacts own copied output layout.
- Future compatibility: original SAMPart3D paths remain in manifest for Phase 5 bridge work.

## Completion Criteria

- `04-SUMMARY.md` records implementation and verification results.
- `04-VERIFICATION.md` records automated checks and real-run result or prerequisite blocker.
- ROADMAP marks Phase 4 complete only if real SAMPart3D run produces or locates `mesh_1.0.npy`.
- If prerequisites are missing, Phase 4 execution should stop with a clear blocker instead of being marked complete.

# Environment Strategy

## Decision

PartPipeline will use an **environment dispatcher** for v1.

The user-facing command remains unified through PartPipeline, but internal subprocesses run with the environment that already supports each model stack:

| Step | Environment | Python |
|------|-------------|--------|
| SAMPart3D | `part` | `/home/rui/miniconda3/envs/part/bin/python` |
| HoloPart | `holopart` | `/home/rui/miniconda3/envs/holopart/bin/python` |

This satisfies ENV-01 and ENV-02: the shared-env feasibility has been checked, and the fallback keeps one PartPipeline command as the user-facing interface.

## 2026-05-15 Shared Environment Recheck

After correcting the SAMPart3D environment name from `p3sam` to `part`, Phase 2 was rechecked.

Updated conclusion:

- A shared environment is **more plausible than the first pass suggested**, because both `part` and `holopart` currently use `torch 2.1.0+cu121`.
- The existing environments still cannot replace each other directly.
- The safest v1 strategy remains dispatcher.
- If we want to prove a single environment, use a cloned spike env based on `part`, not the live `part` environment.

Why `part` is the better shared-env base:

- `part` already has SAMPart3D's harder pieces: `torch_scatter` and `pointops`.
- With a project-local CUDA symlink directory, SAMPart3D core modules can import individually.
- Missing HoloPart dependencies in `part` are mostly installable Python/wheel dependencies: `torch_cluster`, `diffusers`, `pymeshlab`, plus version checks.

Why it is not proven yet:

- HoloPart pins `numpy==1.22.3`, while `part` has `numpy==1.26.4`.
- HoloPart has different `diffusers`, `transformers`, and `huggingface_hub` versions from `part`.
- Installing HoloPart dependencies directly into `part` could break the currently useful SAMPart3D environment.

Durable recheck details are recorded in:

- `.planning/phases/02-environment-strategy/02-SHARED-ENV-RECHECK.md`

## Probe Method

Phase 2 used lightweight probes only:

- package import/version checks
- `--help` smoke tests
- core import smoke tests

No conda environments were mutated. No heavy model inference, training, rendering, or weight download was run.

The generated JSON probe outputs are local runtime artifacts:

- `outputs/env_probe/part.json`
- `outputs/env_probe/holopart.json`
- `outputs/env_probe/part_recheck.json`
- `outputs/env_probe/holopart_recheck.json`

`outputs/` is intentionally gitignored, so this document captures the durable decision.

## Environment Inventory

| Item | `part` | `holopart` |
|------|--------|------------|
| Python | 3.10.20 | 3.10.20 |
| PyTorch | 2.1.0+cu121 | 2.1.0+cu121 |
| CUDA ABI | 12.1 | 12.1 |
| GPU visible | NVIDIA GeForce RTX 3090 | NVIDIA GeForce RTX 3090 |
| NumPy | 1.26.4 | 1.22.3 |
| trimesh | 4.11.5 | 4.12.1 |
| pymeshlab | missing | 2025.7.post1 |
| diffusers | missing | 0.30.3 |
| transformers | 4.37.2 | 4.44.2 |
| huggingface_hub | 0.36.2 | 0.24.6 |
| torch_cluster | missing | 1.6.3+pt21cu121 |
| torch_scatter | 2.1.2+pt21cu121 | missing |
| pointops | 1.0 | missing |

## Smoke Test Results

| Smoke test | `part` | `holopart` |
|------------|--------|------------|
| SAMPart3D runner `--help` | pass | pass |
| SAMPart3D core import | raw fail: `libcudart.so` loader path; core modules import individually with project-local CUDA symlinks | fail: missing `pointops` |
| HoloPart inference `--help` | fail: missing `pymeshlab` | pass |
| HoloPart core import | fail: missing `diffusers` | pass |

Important notes:

- `part` is closer to a possible shared environment because it already has `torch_scatter` and `pointops`.
- `holopart` is the proven HoloPart runtime because HoloPart imports and CLI help both pass there.
- A cloned shared-env spike is reasonable, but the live v1 pipeline should not depend on it until smoke tests pass.

## Shared Environment Feasibility Matrix

| Criterion | Result | Signal |
|-----------|--------|--------|
| Python version match | Both are Python 3.10.20 | shared env possible |
| PyTorch/CUDA compatibility | Both are 2.1.0+cu121 | shared env possible |
| compiled extension compatibility | `part` has `torch_scatter`; `holopart` has `torch_cluster`; both are pt21cu121-compatible | shared env possible via cloned env |
| dependency overlap | version differences remain for NumPy/diffusers/transformers/huggingface stack | risk |
| maintenance risk | directly modifying live envs is risky | dispatcher for v1 |
| time to first working pipeline | existing envs already cover their own model side | dispatcher for v1 |

## Dispatcher Contract

Later phases should implement subprocess execution with this contract:

| Field | SAMPart3D | HoloPart |
|-------|-----------|----------|
| repo | `third_party/SAMPart3D` | `third_party/HoloPart` |
| env | `part` | `holopart` |
| python | `/home/rui/miniconda3/envs/part/bin/python` | `/home/rui/miniconda3/envs/holopart/bin/python` |
| cwd | repo root | repo root |
| logs | per-run output folder | per-run output folder |

Each dispatched command should record:

- environment name
- executable path
- working directory
- command argv
- exit code
- stdout/stderr log paths

Errors should surface enough context for the user to rerun the failing command manually.

## Follow-Up For Later Phases

- Phase 4 should implement the SAMPart3D runner using `part`.
- The SAMPart3D runner should manage the CUDA loader symlink/`LD_LIBRARY_PATH` issue without requiring the user to edit the conda environment.
- HoloPart should continue using `holopart` unless a cloned shared-env spike passes.
- A future cleanup phase may promote `partpipeline-shared` only after it passes both SAMPart3D and HoloPart smoke tests.

# Environment Strategy

## Decision

PartPipeline will use an **environment dispatcher** for v1.

The user-facing command remains unified through PartPipeline, but internal subprocesses run with the environment that already supports each model stack:

| Step | Environment | Python |
|------|-------------|--------|
| SAMPart3D | `p3sam` | `/home/rui/miniconda3/envs/p3sam/bin/python` |
| HoloPart | `holopart` | `/home/rui/miniconda3/envs/holopart/bin/python` |

This satisfies ENV-01 and ENV-02: the shared-env feasibility has been checked, and the fallback keeps one PartPipeline command as the user-facing interface.

## Probe Method

Phase 2 used lightweight probes only:

- package import/version checks
- `--help` smoke tests
- core import smoke tests

No conda environments were mutated. No heavy model inference, training, rendering, or weight download was run.

The generated JSON probe outputs are local runtime artifacts:

- `outputs/env_probe/p3sam.json`
- `outputs/env_probe/holopart.json`

`outputs/` is intentionally gitignored, so this document captures the durable decision.

## Environment Inventory

| Item | `p3sam` | `holopart` |
|------|---------|------------|
| Python | 3.10.20 | 3.10.20 |
| PyTorch | 2.4.0+cu124 | 2.1.0+cu121 |
| CUDA ABI | 12.4 | 12.1 |
| GPU visible | NVIDIA GeForce RTX 3090 | NVIDIA GeForce RTX 3090 |
| NumPy | 1.26.4 | 1.22.3 |
| trimesh | 4.11.5 | 4.12.1 |
| pymeshlab | 2025.7.post1 | 2025.7.post1 |
| diffusers | 0.37.1 | 0.30.3 |
| transformers | 4.41.2 | 4.44.2 |
| huggingface_hub | 0.36.2 | 0.24.6 |
| torch_cluster | missing | 1.6.3+pt21cu121 |
| torch_scatter | 2.1.2+pt24cu124 | missing |
| torch_sparse | missing | missing |

## Smoke Test Results

| Smoke test | `p3sam` | `holopart` |
|------------|---------|------------|
| SAMPart3D runner `--help` | pass | pass |
| SAMPart3D core import | fail: `libnvrtc.so.12` not on loader path | fail: missing `pointops` |
| HoloPart inference `--help` | fail: missing `torch_cluster` | pass |
| HoloPart core import | fail: diffusers import chain failure | pass |

Important notes:

- `p3sam` is closer to SAMPart3D because it has `torch_scatter` for PyTorch 2.4/CUDA 12.4 and already has the SAMPart3D runner in the fork.
- `holopart` is the correct HoloPart runtime because HoloPart imports and CLI help both pass there.
- A single shared environment would need to reconcile different PyTorch/CUDA compiled extension stacks: `torch_scatter` for PyTorch 2.4/CUDA 12.4 versus `torch_cluster` for PyTorch 2.1/CUDA 12.1.

## Shared Environment Feasibility Matrix

| Criterion | Result | Signal |
|-----------|--------|--------|
| Python version match | Both are Python 3.10.20 | shared env possible |
| PyTorch/CUDA compatibility | 2.4.0+cu124 vs 2.1.0+cu121 | dispatcher |
| compiled extension compatibility | different torch extension wheels are installed/missing | dispatcher |
| dependency overlap | overlap exists, but versions differ for NumPy/diffusers/huggingface stack | dispatcher |
| maintenance risk | shared env would require rebuilding fragile compiled dependencies | dispatcher |
| time to first working pipeline | existing envs already cover their own model side | dispatcher |

## Dispatcher Contract

Later phases should implement subprocess execution with this contract:

| Field | SAMPart3D | HoloPart |
|-------|-----------|----------|
| repo | `third_party/SAMPart3D` | `third_party/HoloPart` |
| env | `p3sam` | `holopart` |
| python | `/home/rui/miniconda3/envs/p3sam/bin/python` | `/home/rui/miniconda3/envs/holopart/bin/python` |
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

- Phase 3 should add a SAMPart3D command runner using `p3sam`.
- Phase 4 should remain environment-light and use whichever PartPipeline environment is active for mesh/mask conversion.
- Phase 5 should add a HoloPart command runner using `holopart`.
- A future cleanup phase may revisit a shared environment after the full pipeline works end to end.

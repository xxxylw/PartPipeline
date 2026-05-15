---
phase: 2
phase_name: Environment Strategy
status: planned
requirements_addressed:
  - ENV-01
  - ENV-02
---

# Phase 2 Plan: Environment Strategy

## Objective

Determine whether SAMPart3D and HoloPart can safely share one conda environment. If not, document and prepare the env-dispatcher strategy while keeping the user-facing PartPipeline command unified.

## Non-Goals

- Do not install or upgrade heavy dependencies during this phase.
- Do not run full SAMPart3D rendering/training/eval.
- Do not run full HoloPart model inference or download model weights.
- Do not mutate the existing `p3sam` or `holopart` environments.

## Wave 1: Environment Inventory

### Task 1: Capture conda environment facts

Collect machine-readable facts for both environments:

- Python version
- executable path
- conda prefix
- PyTorch version
- CUDA availability and `torch.version.cuda`
- GPU count/name if visible
- installed versions for key packages:
  - `torch`, `torchvision`, `torchaudio`
  - `torch_cluster`, `torch_scatter`, `torch_sparse`
  - `trimesh`, `numpy`, `pymeshlab`
  - `diffusers`, `transformers`, `huggingface_hub`
  - `pointcept` import availability if applicable

Expected artifact:

- `docs/environment-strategy.md` with an inventory table.

Suggested commands:

```bash
/home/rui/miniconda3/envs/p3sam/bin/python scripts/probe_env.py --json outputs/env_probe/p3sam.json
/home/rui/miniconda3/envs/holopart/bin/python scripts/probe_env.py --json outputs/env_probe/holopart.json
```

### Task 2: Compare project requirements

Read and summarize:

- `third_party/SAMPart3D/requirements.txt`
- `third_party/HoloPart/requirements.txt`
- any install notes that directly affect runtime compatibility

Expected artifact:

- `docs/environment-strategy.md` includes a dependency comparison section.

## Wave 2: Smoke Tests

### Task 3: SAMPart3D import smoke test

In `p3sam`, verify imports needed before full execution:

- Python can import standard runtime dependencies.
- `third_party/SAMPart3D/tools/run_sampart3d_object.py --help` works.
- SAMPart3D launch/config modules can be imported enough to catch missing packages.

Pass criteria:

- Help command exits 0.
- Required imports either pass or produce a documented missing-package error.

### Task 4: HoloPart import smoke test

In `holopart`, verify imports needed before full execution:

- Python can import `trimesh`, `pymeshlab`, `torch`, `diffusers`, `huggingface_hub`.
- `third_party/HoloPart/scripts/inference_holopart.py --help` works if import-time dependencies allow it.
- `holopart.pipelines.pipeline_holopart` and `holopart.inference_utils` imports are tested without running inference.

Pass criteria:

- Help/import checks either pass or produce a documented missing-package error.
- No model weights are downloaded during this phase.

## Wave 3: Shared Environment Feasibility Decision

### Task 5: Score shared-env feasibility

Create a decision matrix with these criteria:

| Criterion | Shared Env Signal | Dispatcher Signal |
|-----------|-------------------|-------------------|
| Python version match | Same minor version | Different minor versions |
| PyTorch/CUDA compatibility | Same torch/CUDA ABI | Different torch/CUDA ABI |
| compiled extension compatibility | same torch-cluster/scatter needs | incompatible compiled wheels |
| dependency overlap | mostly same packages | conflicting package pins |
| maintenance risk | low | medium/high |
| time to first working pipeline | quick | dispatcher faster |

Decision rule:

- Choose shared env only if no major ABI conflicts appear and import smoke tests pass in one candidate env with minimal additions.
- Otherwise choose dispatcher.

Expected artifact:

- `docs/environment-strategy.md` records the decision and rationale.

## Wave 4: Dispatcher Contract

### Task 6: Define dispatcher interface

If dispatcher is selected, document the contract PartPipeline will implement later:

- `sampart3d.env`: `p3sam`
- `holopart.env`: `holopart`
- commands are launched via conda environment-specific Python paths or `conda run`
- each subprocess receives explicit `cwd`, `PYTHONPATH`, and log path
- errors surface command, env, exit code, and log file

Expected artifact:

- `configs/default.yaml` remains or is updated with the selected env strategy.
- `docs/environment-strategy.md` includes dispatcher command examples.

## Verification

Run these checks before marking Phase 2 complete:

```bash
cd /home/rui/of_work/code/PartPipeline
git status --short
/home/rui/miniconda3/envs/p3sam/bin/python -m py_compile src/partpipeline/cli.py
/home/rui/miniconda3/envs/p3sam/bin/python scripts/probe_env.py --json /tmp/p3sam_probe.json
/home/rui/miniconda3/envs/holopart/bin/python scripts/probe_env.py --json /tmp/holopart_probe.json
```

If `scripts/probe_env.py` does not exist yet, creating it is part of Phase 2 execution.

## Completion Criteria

- ENV-01: A document states whether shared env works or dispatcher is required.
- ENV-02: The selected strategy keeps PartPipeline as the single user-facing command.
- No existing conda environment was mutated.
- Any failed imports are documented with exact error messages.
- The next phase can safely implement SAMPart3D invocation using the chosen strategy.

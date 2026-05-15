# Phase 4 Summary: SAMPart3D Integration

## Status

Complete.

PartPipeline can now run SAMPart3D for a single `.glb`, using the `part` conda environment, and locate/copy the default selected result `mesh_1.0.npy`.

## Completed

- Added `src/partpipeline/runners/sampart3d.py`.
- Added SAMPart3D result/path dataclasses in `src/partpipeline/types.py`.
- Added selected mask copy helper in `src/partpipeline/artifacts.py`.
- Wired non-dry-run orchestration to `Sampart3DRunner`.
- Preserved dry-run behavior with a real SAMPart3D command contract.
- Added CUDA loader symlink setup under `outputs/run_state/part_cuda_lib/`.
- Added preflight checks for:
  - input GLB
  - SAMPart3D repo
  - wrapper script
  - config template
  - `part` Python
  - Blender
  - backbone weight
  - CUDA torch libraries
- Linked existing local SAMPart3D prerequisites into the PartPipeline submodule:
  - `third_party/SAMPart3D/blender-4.0.0-linux-x64`
  - `third_party/SAMPart3D/ckpt`
- Added staging for input GLBs before calling SAMPart3D. This avoids SAMPart3D train/eval path mismatches when source filenames contain spaces or non-ASCII display names.
- Added `docs/sampart3d-integration.md`.
- Added tests for runner command construction, staged input naming, CUDA symlinks, preflight failure, mask copying, artifacts, and orchestrator manifest success.

## Real Run

Command:

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb"
```

Result:

```text
Profile: local_wsl
Status: sampart3d_complete
Run directory: /home/rui/of_work/code/PartPipeline/outputs/runs/08.toulouse-20260515-160213
Manifest: /home/rui/of_work/code/PartPipeline/outputs/runs/08.toulouse-20260515-160213/manifest.json
```

Selected SAMPart3D output:

```text
third_party/SAMPart3D/exp/sampart3d/08.toulouse-20260515-160213/results/5000/mesh_1.0.npy
```

Copied PartPipeline artifact:

```text
outputs/runs/08.toulouse-20260515-160213/sam/mesh_1.0.npy
```

## Verification Summary

Automated verification passed:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
/home/rui/miniconda3/envs/part/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py
```

Result:

- 22 tests passed.
- Real SAMPart3D run passed.
- `mesh_1.0.npy` was produced and copied into the PartPipeline run folder.

## Next Phase

Proceed to Phase 5: convert `input.glb + mesh_1.0.npy` into a HoloPart-compatible multipart GLB scene.

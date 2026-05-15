# Phase 4 Summary: SAMPart3D Integration

## Status

Implementation complete for the PartPipeline-side SAMPart3D runner, but Phase 4 is not fully complete because the real SAMPart3D run is blocked by missing local prerequisites:

- `third_party/SAMPart3D/blender-4.0.0-linux-x64/blender`
- `third_party/SAMPart3D/ckpt/ptv3-object.pth`

The implementation correctly fails at preflight and writes a failed manifest instead of mutating environments or downloading resources.

## Completed

- Added `src/partpipeline/runners/sampart3d.py`.
- Added SAMPart3D result/path dataclasses in `src/partpipeline/types.py`.
- Added selected mask copy helper in `src/partpipeline/artifacts.py`.
- Wired non-dry-run orchestration to `Sampart3DRunner`.
- Preserved dry-run behavior with a real SAMPart3D command contract.
- Added CUDA loader symlink setup under `outputs/run_state/part_cuda_lib/`.
- Added clear preflight checks for:
  - input GLB
  - SAMPart3D repo
  - wrapper script
  - config template
  - `part` Python
  - Blender
  - backbone weight
  - CUDA torch libraries
- Added `docs/sampart3d-integration.md`.
- Added tests for runner command construction, CUDA symlinks, preflight failure, mask copying, artifacts, and orchestrator manifest success.

## Verification Summary

Automated verification passed:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
/home/rui/miniconda3/envs/part/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli --help
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb" --dry-run
```

Result:

- 21 tests passed.
- CLI help passed.
- Dry-run passed.
- Real-run preflight failed correctly due to missing Blender and SAMPart3D backbone weight.

## Next Required User/System Action

Place or link the required SAMPart3D prerequisites into the expected paths:

```text
third_party/SAMPart3D/blender-4.0.0-linux-x64/blender
third_party/SAMPart3D/ckpt/ptv3-object.pth
```

Then rerun:

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb"
```

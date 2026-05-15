# SAMPart3D Integration

Phase 4 connects PartPipeline's single-file `run` command to SAMPart3D. It runs SAMPart3D through the `part` conda environment and records the selected segmentation mask, defaulting to `mesh_1.0.npy`.

This phase does not run HoloPart, does not convert the mask into a multipart GLB, and does not process batches.

## Command Flow

PartPipeline calls:

```bash
/home/rui/miniconda3/envs/part/bin/python third_party/SAMPart3D/tools/run_sampart3d_object.py --glb <input.glb>
```

The runner passes an explicit experiment name based on the PartPipeline run directory. SAMPart3D writes original outputs under:

```text
third_party/SAMPart3D/exp/sampart3d/<exp-name>/
```

PartPipeline copies the selected mask into:

```text
outputs/runs/<run>/sam/mesh_1.0.npy
```

The manifest records both the copied PartPipeline path and the original SAMPart3D paths.

## Prerequisites

The runner checks these before a real model run:

- input `.glb`
- `third_party/SAMPart3D/tools/run_sampart3d_object.py`
- `/home/rui/miniconda3/envs/part/bin/python`
- `third_party/SAMPart3D/blender-4.0.0-linux-x64/blender`
- `third_party/SAMPart3D/ckpt/ptv3-object.pth`
- CUDA runtime libraries in the `part` environment's torch library folder

If any prerequisite is missing, the CLI fails clearly and writes a failed manifest when a run directory has been created. It does not download files, install packages, or modify conda environments.

## CUDA Loader

The `part` environment ships hashed CUDA library names in torch's library folder. The SAMPart3D runner creates project-local symlinks under:

```text
outputs/run_state/part_cuda_lib/
```

It then prepends that directory and torch's library directory to `LD_LIBRARY_PATH`.

## Verification

Automated tests cover command construction, preflight, CUDA loader setup, result copying, and manifest writing without running the heavy model. A real verification run should be launched only after Blender and `ptv3-object.pth` are present.

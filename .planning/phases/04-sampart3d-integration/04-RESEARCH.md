# Phase 4 Research: SAMPart3D Integration

## Goal

Integrate SAMPart3D as the first real model step in PartPipeline. A single `.glb` should trigger SAMPart3D through the layered runner and locate the selected mask result, defaulting to `mesh_1.0.npy`.

## SAMPart3D Entrypoint

Use:

```bash
/home/rui/miniconda3/envs/part/bin/python third_party/SAMPart3D/tools/run_sampart3d_object.py --glb <input.glb>
```

The wrapper supports:

- `--glb`
- `--exp-name`
- `--gpu`
- `--num-gpus`
- `--blender`
- `--backbone-weight`
- `--config-template`
- `--weight-name`
- `--skip-render`
- `--skip-train`
- `--skip-eval`

Phase 4 should not use skip flags for the real verification path because the user selected a complete SAMPart3D run.

## Wrapper Behavior

`run_sampart3d_object.py`:

1. Validates input `.glb`.
2. Uses repo-local defaults:
   - Blender: `<SAMPart3D>/blender-4.0.0-linux-x64/blender`
   - Backbone weight: `<SAMPart3D>/ckpt/ptv3-object.pth`
   - Config template: `configs/sampart3d/sampart3d-trainmlp-render16views.py`
   - Eval weight name: `5000`
3. Copies the source GLB into `<SAMPart3D>/mesh_root/<object>.glb`.
4. Generates a per-object config at `<SAMPart3D>/exp/sampart3d/<exp-name>/config.py`.
5. Runs render, train, and eval.
6. Reports:
   - Config: `<SAMPart3D>/exp/sampart3d/<exp-name>/config.py`
   - Renders: `<SAMPart3D>/data_root/<object>`
   - Results: `<SAMPart3D>/exp/sampart3d/<exp-name>/results/<weight-name>`
   - Meshes/visualization: `<SAMPart3D>/exp/sampart3d/<exp-name>/vis_pcd/<weight-name>`

The selected v1 output is expected at:

```text
<SAMPart3D>/exp/sampart3d/<exp-name>/results/5000/mesh_1.0.npy
```

## Runtime Findings

SAMPart3D uses the `part` conda environment:

```text
/home/rui/miniconda3/envs/part/bin/python
```

The environment has the SAMPart3D-side compiled pieces:

- `torch==2.1.0+cu121`
- `torch-scatter==2.1.2+pt21cu121`
- `pointops==1.0`

The current CUDA loader issue can be addressed without mutating the conda environment:

- Torch ships hashed libraries such as `libcudart-9335f6a2.so.12` and `libnvrtc-b51b459d.so.12`.
- Some SAMPart3D imports look for stable names such as `libcudart.so` / `libnvrtc.so`.
- A project-local symlink directory under `outputs/run_state/part_cuda_lib/` plus `LD_LIBRARY_PATH` can make core SAMPart3D modules import.

## Current Prerequisite Risk

A quick repository scan did not show these defaults in the submodule:

- `third_party/SAMPart3D/ckpt/ptv3-object.pth`
- `third_party/SAMPart3D/blender-4.0.0-linux-x64/blender`

Phase 4 must therefore implement explicit preflight checks and clear failures. It should not download weights, install Blender, or mutate conda environments.

## Implementation Implications

- Add `src/partpipeline/runners/sampart3d.py`.
- Keep subprocess execution through `SubprocessRunner`.
- Add preflight functions for GLB, wrapper script, config template, Blender, backbone weight, Python executable, and CUDA symlink source libraries.
- Add result discovery for `mesh_<mask-scale>.npy`, defaulting to `mesh_1.0.npy`.
- Copy the selected mask into the PartPipeline run folder under `sam/`.
- Record both original SAMPart3D paths and PartPipeline artifact paths in `manifest.json`.
- Preserve `--dry-run` behavior for no-model tests.

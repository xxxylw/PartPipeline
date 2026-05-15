# Phase 4 Verification

## Result

PARTIAL / BLOCKED.

The PartPipeline-side SAMPart3D integration is implemented and automatically verified. The real full SAMPart3D run did not start because preflight found missing local resources.

## Automated Checks

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
```

Result: PASS, 21 tests.

```bash
/home/rui/miniconda3/envs/part/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py
```

Result: PASS.

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli --help
```

Result: PASS.

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb" --dry-run
```

Result: PASS. A dry-run manifest was created and recorded a SAMPart3D command using the `part` profile.

## Real-Run Preflight

Command attempted:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb"
```

Observed blocker:

```text
SAMPart3D preflight failed:
- Blender executable missing: /home/rui/of_work/code/PartPipeline/third_party/SAMPart3D/blender-4.0.0-linux-x64/blender
- SAMPart3D backbone weight missing: /home/rui/of_work/code/PartPipeline/third_party/SAMPart3D/ckpt/ptv3-object.pth
```

The failed run manifest was written under:

```text
outputs/runs/08.toulouse-20260515-154348/manifest.json
```

Manifest behavior verified:

- `status`: `failed`
- `error.type`: `preflight`
- `error.issues`: lists missing Blender and missing `ptv3-object.pth`
- no dependency install or resource download was attempted

## Requirement Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| CLI-01 | PARTIAL | Single-file command reaches the SAMPart3D runner and preflight. Full model execution is blocked by missing local resources. |
| CLI-03 | COVERED for implementation | Mask scale controls selected result path, defaulting to `mesh_1.0.npy`; tested without model execution. |
| BRIDGE-01 | PARTIAL | Code can predict and copy `mesh_1.0.npy` when produced; real file not produced yet because full SAMPart3D run is blocked. |

## Completion Gate

Do not mark Phase 4 complete until a real run produces or locates:

```text
third_party/SAMPart3D/exp/sampart3d/<exp-name>/results/5000/mesh_1.0.npy
```

and copies it into:

```text
outputs/runs/<run>/sam/mesh_1.0.npy
```

# Phase 4 Verification

## Result

PASS.

The real SAMPart3D run completed and produced the default selected segmentation result `mesh_1.0.npy`.

## Automated Checks

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
```

Result: PASS, 22 tests.

```bash
/home/rui/miniconda3/envs/part/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py
```

Result: PASS.

## Real Run Verification

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

Verified files:

```text
/home/rui/of_work/code/PartPipeline/third_party/SAMPart3D/exp/sampart3d/08.toulouse-20260515-160213/results/5000/mesh_1.0.npy
/home/rui/of_work/code/PartPipeline/outputs/runs/08.toulouse-20260515-160213/sam/mesh_1.0.npy
```

The copied PartPipeline artifact is about 7.6 MB.

## Requirement Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| CLI-01 | COVERED for SAMPart3D stage | A single GLB can trigger SAMPart3D through the PartPipeline command. Full end-to-end pipeline continues in later phases. |
| CLI-03 | COVERED | Mask scale defaults to `1.0`; the selected result path is `mesh_1.0.npy`, and the override path is covered by tests. |
| BRIDGE-01 | COVERED | PartPipeline locates and copies SAMPart3D output `mesh_1.0.npy`. |

## Notes

The first real run exposed a filename mismatch when the input GLB stem contained spaces. The runner now stages the source GLB to a space-free filename inside the PartPipeline run directory before calling SAMPart3D. This keeps SAMPart3D render/train/eval object names aligned.

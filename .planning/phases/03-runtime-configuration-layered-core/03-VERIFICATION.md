# Phase 3 Verification

## Result

PASS. Phase 3 created the model-free runtime core and verified it without running SAMPart3D or HoloPart.

## Requirement Coverage

| Requirement | Phase 3 Result |
|-------------|----------------|
| CLI-01 | Partially satisfied: `partpipeline run <glb> --dry-run` now prepares one run and writes a manifest. Full model execution remains Phase 4-6. |
| CLI-02 | Partially satisfied: `partpipeline batch <dir>` loads config/profile and counts GLBs. Full batch processing remains Phase 7. |
| CLI-03 | Partially satisfied: mask scale defaults to config value `1.0` and can be overridden at run preparation time. SAMPart3D scale selection is completed in Phase 4. |
| OUT-01 | Partially satisfied: manifest contract and run directories exist. Final output path and timings arrive with model execution phases. |
| ENV-02 | Maintained: user-facing CLI stays unified while profiles preserve the dispatcher strategy. |

## Checks

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
```

Result: 12 tests passed.

```bash
/home/rui/miniconda3/envs/part/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py
```

Result: passed.

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli --help
```

Result: passed; commands `run` and `batch` are visible.

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb" --dry-run
```

Result: passed; manifest created under `outputs/runs/`.

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb" --profile server --output-dir outputs/server-runs --dry-run
```

Result: passed; server profile loaded without touching server filesystem.

## Residual Risk

- The SAMPart3D command is still a placeholder contract. Phase 4 must replace it with the real invocation and solve the CUDA loader issue found during Phase 2.
- Server paths are intentionally placeholders. Before server execution, inspect `d5` and update `configs/default.yaml`.

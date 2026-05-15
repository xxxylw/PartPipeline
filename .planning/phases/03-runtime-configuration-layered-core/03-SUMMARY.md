# Phase 3 Summary: Runtime Configuration and Layered Core

## Completed

- Reworked `configs/default.yaml` into profile-based runtime config with `local_wsl` and `server` profiles.
- Recorded server SSH identity for `d5`:
  - HostName: `10.1.6.8`
  - User: `qzqd5`
  - Port: `19091`
- Added layered runtime modules:
  - CLI: `src/partpipeline/cli.py`
  - config/profile: `src/partpipeline/config.py`
  - orchestration: `src/partpipeline/orchestrator.py`
  - subprocess runner: `src/partpipeline/runners/base.py`
  - artifacts/manifest: `src/partpipeline/artifacts.py`
  - domain types: `src/partpipeline/types.py`
- Added dry-run manifest creation for single GLB runs.
- Added batch command scaffolding that loads the same config/profile layer.
- Added tests for config, artifacts, runner, and orchestration without GPU/model execution.
- Documented the runtime core in `docs/runtime-core.md`.

## Notes

Phase 3 intentionally does not execute SAMPart3D or HoloPart. The manifest records a future SAMPart3D command contract so Phase 4 can replace the placeholder with the real runner without changing CLI or artifact layout.

The server profile is usable for config loading and dry-run planning. Its filesystem paths remain placeholders until the `d5` server is inspected.

## Verification

All planned checks passed on 2026-05-15:

```bash
/home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
/home/rui/miniconda3/envs/part/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli --help
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb" --dry-run
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb" --profile server --output-dir outputs/server-runs --dry-run
```

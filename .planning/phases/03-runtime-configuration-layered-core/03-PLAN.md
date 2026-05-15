---
phase: 3
phase_name: Runtime Configuration and Layered Core
status: planned
wave: 1
requirements_addressed:
  - CLI-01
  - CLI-02
  - CLI-03
  - OUT-01
  - ENV-02
files_modified:
  - configs/default.yaml
  - src/partpipeline/cli.py
  - src/partpipeline/config.py
  - src/partpipeline/types.py
  - src/partpipeline/artifacts.py
  - src/partpipeline/orchestrator.py
  - src/partpipeline/runners/base.py
  - src/partpipeline/runners/__init__.py
  - tests/test_config.py
  - tests/test_artifacts.py
  - tests/test_runner.py
  - tests/test_orchestrator.py
  - docs/runtime-core.md
---

# Phase 3 Plan: Runtime Configuration and Layered Core

## Objective

Build the model-free runtime core that later SAMPart3D and HoloPart integrations will use: profile-based YAML config, simple layered modules, run artifact creation, manifest writing, and a subprocess runner contract. Phase 3 must not execute SAMPart3D or HoloPart.

## Must-Haves

- Preserve the dispatcher decision from Phase 2.
- Use YAML configuration with `local_wsl` and `server` profiles.
- Include server SSH identity in config or docs:
  - Host alias: `d5`
  - HostName: `10.1.6.8`
  - User: `qzqd5`
  - Port: `19091`
- Keep filesystem paths and Python executables configurable; do not hardcode WSL assumptions in orchestration logic.
- Keep code split into simple layers:
  - CLI
  - config/profile
  - orchestration
  - runner/subprocess
  - artifacts/manifest
  - domain/types
- Add tests for each layer without requiring GPU or model execution.

## Non-Goals

- Do not run SAMPart3D.
- Do not run HoloPart.
- Do not inspect or mutate the server filesystem.
- Do not install dependencies or modify conda environments.
- Do not implement mask conversion or HoloPart input preparation.

## Wave 1: Config and Domain Types

### Task 1: Add profile-based YAML config

Update `configs/default.yaml` from flat local paths to a profile structure:

- `active_profile: local_wsl`
- `profiles.local_wsl`
- `profiles.server`
- `environment.strategy: dispatcher`
- `pipeline.default_mask_scale: "1.0"`

The `local_wsl` profile should keep the known local paths. The `server` profile should include known SSH identity and placeholder path values for later inspection.

Acceptance criteria:

- The config file is valid YAML.
- Both profiles contain repo paths, Python executable paths, output root, and model-specific settings.
- Server profile clearly marks unknown filesystem paths as placeholders.

### Task 2: Implement config/profile layer

Create `src/partpipeline/config.py` with:

- `load_config(path: Path) -> PipelineConfig`
- `resolve_profile(config: PipelineConfig, profile_name: str | None) -> RuntimeProfile`
- path resolution relative to project root for repo/output paths when appropriate
- helpful errors for missing config, missing profile, and missing required keys

Use dataclasses or lightweight typed structures from `types.py`. Avoid heavy config frameworks.

Acceptance criteria:

- `local_wsl` profile loads by default.
- `server` profile loads by explicit name.
- tests cover missing profile and relative path resolution.

### Task 3: Add domain/types layer

Create `src/partpipeline/types.py` with simple dataclasses for:

- `ToolRuntime`
- `RuntimeProfile`
- `PipelineConfig`
- `RunRequest`
- `RunPaths`
- `CommandResult`
- `RunManifest`

Acceptance criteria:

- Types are plain dataclasses or typed dictionaries, easy to serialize where needed.
- No model-specific execution logic lives in this file.

## Wave 2: Artifacts and Runner Contract

### Task 4: Implement artifact/manifest layer

Create `src/partpipeline/artifacts.py` with helpers to:

- create run directory names like `<asset-stem>-YYYYMMDD-HHMMSS`
- create subdirectories: `logs/`, `sam/`, `prepared/`, `holopart/`
- write `manifest.json`
- update manifest status and selected mask scale

Acceptance criteria:

- Artifact creation works without model execution.
- Manifest includes input path, profile, output root, run directory, mask scale, status, timestamps, and paths.
- tests verify directory layout and manifest JSON contents.

### Task 5: Implement subprocess runner base

Create `src/partpipeline/runners/base.py` with a model-agnostic runner that can:

- execute an argv list with explicit `cwd`
- merge environment variables
- write stdout/stderr to log files
- return `CommandResult`
- support `dry_run=True` to record the command without executing it

Acceptance criteria:

- tests use simple Python commands, not model commands.
- dry-run returns a result with command/cwd/log path metadata and does not execute.
- nonzero exit codes are captured, not swallowed.

## Wave 3: Orchestration and CLI Wiring

### Task 6: Implement model-free orchestration skeleton

Create `src/partpipeline/orchestrator.py` with:

- `prepare_single_run(request: RunRequest) -> RunManifest`
- config/profile resolution
- artifact directory creation
- manifest writing
- optional dry-run command contract placeholders for future SAMPart3D integration

Acceptance criteria:

- Running orchestration for an existing `.glb` creates a run folder and manifest.
- No SAMPart3D/HoloPart subprocess is invoked.
- tests verify orchestration delegates config/artifact responsibilities cleanly.

### Task 7: Wire CLI to orchestration

Update `src/partpipeline/cli.py`:

- add `--config configs/default.yaml`
- add `--profile local_wsl|server`
- keep `--output-dir`
- keep `--mask-scale`, defaulting to config value if omitted
- add `--dry-run` for Phase 3-safe execution
- `run` calls orchestration and prints manifest/run directory
- `batch` may remain scaffolded but should load config/profile and count GLBs using the same config layer

Acceptance criteria:

- `partpipeline run <glb> --dry-run` creates artifacts and manifest.
- `partpipeline run <glb> --profile server --dry-run` can load server profile without requiring server paths to exist.
- CLI does not contain subprocess or artifact layout internals.

## Wave 4: Documentation and Verification

### Task 8: Document runtime core

Create `docs/runtime-core.md` describing:

- layer responsibilities
- profile structure
- local WSL versus server profile intent
- server SSH identity for `d5`
- run artifact layout
- how future SAMPart3D/HoloPart integrations plug into runners

Acceptance criteria:

- The doc makes clear Phase 3 does not execute models.
- Server filesystem paths are documented as placeholders until inspected.

### Task 9: Verification

Run automated checks:

```bash
cd /home/rui/of_work/code/PartPipeline
/home/rui/miniconda3/envs/p3sam/bin/python -m unittest discover -s tests
/home/rui/miniconda3/envs/p3sam/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py
PYTHONPATH=src /home/rui/miniconda3/envs/p3sam/bin/python -m partpipeline.cli --help
PYTHONPATH=src /home/rui/miniconda3/envs/p3sam/bin/python -m partpipeline.cli run "/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb" --dry-run
```

Expected result:

- Tests pass.
- CLI help works.
- Dry-run creates a manifest and run artifact folders.
- No model subprocess execution occurs.

## Completion Criteria

- Phase 3 success criteria in ROADMAP are satisfied.
- `03-SUMMARY.md` records implemented layers and verification results.
- `03-VERIFICATION.md` confirms ENV-02/CLI/OUT requirements touched by this phase.
- Changes are committed and pushed.

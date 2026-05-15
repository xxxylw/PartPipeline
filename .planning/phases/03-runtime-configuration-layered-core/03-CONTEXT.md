# Phase 3 Context: Runtime Configuration and Layered Core

## Domain

This phase builds the runtime configuration and layered application core that later model integrations will use. It should not run SAMPart3D or HoloPart yet.

## Decisions

- Use YAML for configuration.
- Keep Phase 3 model-free: do not run SAMPart3D in this phase.
- Add profile-based configuration with at least `local_wsl` and `server` profiles.
- Server profile can use placeholder filesystem paths for now, but SSH identity is known:
  - Host alias: `d5`
  - HostName: `10.1.6.8`
  - User: `qzqd5`
  - Port: `19091`
- Design code in simple layers instead of a single script:
  - CLI layer
  - config/profile layer
  - orchestration layer
  - runner/subprocess layer
  - artifacts/manifest layer
  - domain/types layer
- Paths, Python executables, repository roots, and output roots must come from config or CLI options, not hardcoded WSL assumptions.
- Phase 3 should be testable without GPU/model execution.

## Code Context

Current code is a thin CLI scaffold in `src/partpipeline/cli.py`. Phase 2 selected dispatcher strategy and added `configs/default.yaml` with local WSL Python paths. Phase 3 should reshape this into profile-based config while preserving the dispatcher decision.

## Canonical Refs

- `.planning/PROJECT.md` - project purpose and constraints.
- `.planning/ROADMAP.md` - phase sequence.
- `.planning/REQUIREMENTS.md` - CLI and output requirements.
- `.planning/phases/02-environment-strategy/02-SUMMARY.md` - dispatcher decision.
- `docs/environment-strategy.md` - environment contract.
- `configs/default.yaml` - current config to migrate to profile structure.

## Deferred Ideas

- Real server filesystem paths and conda env paths will be finalized when the server environment is inspected.
- Actual SAMPart3D execution begins in Phase 4.

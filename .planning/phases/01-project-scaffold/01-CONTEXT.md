# Phase 1 Context: Project Scaffold and Repository Wiring

## Domain

This phase creates the project shell and dependency wiring only. It should not attempt model execution.

## Decisions

- Project name: `PartPipeline`.
- Project path: `/home/rui/of_work/code/PartPipeline`.
- Dependency strategy: use submodules under `third_party/` pointing to user forks.
- SAMPart3D fork: `https://github.com/xxxylw/SAMPart3D.git`.
- HoloPart fork: `https://github.com/xxxylw/HoloPart.git`.
- CLI shape: support both `run` for one GLB and `batch` for a directory.
- Default mask scale: `1.0`.
- Model execution is deferred to later phases.

## Code Context

- Existing WSL source repos live under `/home/rui/of_work/code`.
- Existing sample input GLBs live under `/mnt/d/of_work/resources/Disassembled parts` when accessed from WSL.

## Canonical Refs

- `.planning/PROJECT.md` - project context.
- `.planning/REQUIREMENTS.md` - v1 requirements.
- `.planning/ROADMAP.md` - phase structure.

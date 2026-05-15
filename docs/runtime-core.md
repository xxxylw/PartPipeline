# Runtime Core

Phase 3 adds the model-free runtime layer for PartPipeline. It prepares runs, writes manifests, and records future command contracts, but it does not execute SAMPart3D or HoloPart.

## Layers

- CLI: `src/partpipeline/cli.py` parses user commands and delegates work.
- Config/profile: `src/partpipeline/config.py` loads YAML profiles and resolves paths.
- Domain types: `src/partpipeline/types.py` keeps shared dataclasses.
- Artifacts: `src/partpipeline/artifacts.py` creates run folders and `manifest.json`.
- Runner: `src/partpipeline/runners/base.py` provides a model-agnostic subprocess contract.
- Orchestration: `src/partpipeline/orchestrator.py` coordinates config, artifacts, and planned command metadata.

## Profiles

`configs/default.yaml` has two profiles:

- `local_wsl`: the current WSL development layout under `/home/rui/of_work/code/PartPipeline`.
- `server`: a deployment template. The SSH identity is known, while filesystem paths are placeholders until the server is inspected.

Known server SSH identity:

```ssh-config
Host d5
  HostName 10.1.6.8
  User qzqd5
  Port 19091
```

The dispatcher decision from Phase 2 is preserved. SAMPart3D uses the `part` environment and HoloPart uses the `holopart` environment until a shared environment is proven viable.

## Run Artifacts

Each prepared run creates:

```text
<output-root>/<asset-stem>-YYYYMMDD-HHMMSS/
  logs/
  sam/
  prepared/
  holopart/
  manifest.json
```

The manifest records input path, profile, selected mask scale, output root, run directory, status, timestamps, directory layout, and dry-run command metadata.

## Future Integration Points

Phase 4 can replace the SAMPart3D placeholder command with the real segmentation runner while keeping the same manifest and log contract. Later phases can add mask conversion and HoloPart execution without moving artifact layout logic into the CLI.

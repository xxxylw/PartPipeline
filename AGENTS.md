# PartPipeline Agent Guide

This project uses GSD planning documents in `.planning/`.

Key rules:
- Keep SAMPart3D and HoloPart changes inside `third_party/` submodules or their forks.
- Do not commit model weights or generated run outputs.
- Treat `outputs/` as runtime artifacts; keep only `.gitkeep` tracked.
- Preserve the pipeline boundary: PartPipeline orchestrates and converts formats; it should not reimplement the models.

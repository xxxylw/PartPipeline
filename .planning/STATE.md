# State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-15)

**Core value:** A user can provide one `.glb` or a folder of `.glb` files and receive organized, presentation-ready segmented and completed part outputs.
**Current focus:** Phase 7 - Batch, Server Run Mode, and Presentation Outputs

## Last Session

Completed Phase 6 HoloPart integration. PartPipeline can now run `partpipeline holopart <run_dir>` against a Phase 5 bridge output, invoke upstream HoloPart with the `holopart` conda environment, record logs, update `manifest.json`, and collect `holopart/output.glb`. The real run at `outputs/runs/08.toulouse-20260515-160213` completed with status `holopart_complete`; the output GLB is 6.5 MB and loads as a `trimesh.Scene` with 34 geometries. HoloPart weights were predownloaded into the HoloPart submodule because the Python Hugging Face client hit a mirror metadata/cache issue; runtime still sets `HF_ENDPOINT=https://hf-mirror.com`. Next: implement batch processing, server run mode, and presentation-oriented outputs.

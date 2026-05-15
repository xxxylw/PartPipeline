# Phase 5 Summary: Segmentation Bridge Converter

## Status

Complete.

## What Changed

Phase 5 added a `trimesh`-based bridge converter that turns a SAMPart3D face mask plus staged GLB into a HoloPart-compatible multipart GLB.

Implemented:

- `src/partpipeline/bridge.py`
- bridge config under `pipeline.bridge`
- `bridge/` artifact directory per run
- `partpipeline bridge <run_dir>` command for existing SAMPart3D runs
- orchestrator integration after SAMPart3D success
- manifest support for bridge results
- small-part merge logic with topology-first and nearest-centroid fallback

## Real Run

Validated against:

```text
outputs/runs/08.toulouse-20260515-160213
```

Generated:

```text
outputs/runs/08.toulouse-20260515-160213/bridge/prepared_parts.glb
outputs/runs/08.toulouse-20260515-160213/bridge/mesh_1.0_merged.npy
outputs/runs/08.toulouse-20260515-160213/bridge/part_manifest.json
```

Result:

- original part count: 34
- final part count: 34
- merge count: 0
- prepared GLB geometry count: 34
- HoloPart `prepare_data(..., device="cpu")`: passed

The default small-part threshold did not merge any part for this asset because all parts were above the configured threshold.

## Next Phase

Phase 6 should invoke HoloPart on `bridge/prepared_parts.glb` and collect the completed `output.glb`.

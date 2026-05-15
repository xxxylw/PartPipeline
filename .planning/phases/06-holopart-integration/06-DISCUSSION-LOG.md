# Phase 6 Discussion Log: HoloPart Integration

## Summary

The user confirmed the default Phase 6 decisions and asked to enable the HuggingFace mirror for model weight download.

## Decisions

### Scope

Phase 6 will run HoloPart on an existing bridge-complete run:

```text
bridge/prepared_parts.glb -> holopart/output.glb
```

It will not redo SAMPart3D, bridge conversion, batch processing, or server batch orchestration.

### Invocation

Use the upstream HoloPart inference script through a PartPipeline runner:

```text
third_party/HoloPart/scripts/inference_holopart.py
```

Prefer subprocess wrapping over editing HoloPart source.

### Defaults

Use HoloPart's default inference parameters first:

```text
seed=42
num_inference_steps=50
guidance_scale=3.5
batch_size=8
```

### HuggingFace Mirror

Set the HF mirror in the HoloPart runner environment by default:

```text
HF_ENDPOINT=https://hf-mirror.com
```

This should be configurable for local/server profiles.

## Next Step

Run `$gsd-plan-phase 6` to create the implementation plan.

# Phase 6 Research: HoloPart Integration

## Goal

Run HoloPart on the Phase 5 multipart GLB and collect the completed part output in the PartPipeline run directory.

## Current Verified Input

Phase 5 produced and validated:

```text
outputs/runs/08.toulouse-20260515-160213/bridge/prepared_parts.glb
```

HoloPart `prepare_data(..., device="cpu")` successfully loaded the prepared GLB:

```text
part_count 34
whole_cond_shape (34, 20480, 7)
part_cond_shape (34, 20480, 6)
```

This means Phase 6 can focus on HoloPart inference rather than input format conversion.

## HoloPart Invocation

The upstream entrypoint is:

```text
third_party/HoloPart/scripts/inference_holopart.py
```

It accepts:

```text
--mesh-input
--output-dir
--seed
--num-inference-steps
--guidance-scale
--batch_size
```

Recommended invocation shape:

```bash
<holopart-python> scripts/inference_holopart.py \
  --mesh-input <run_dir>/bridge/prepared_parts.glb \
  --output-dir <run_dir>/holopart \
  --seed 42 \
  --num-inference-steps 50 \
  --guidance-scale 3.5 \
  --batch_size 8
```

Run from `third_party/HoloPart` so relative paths such as `pretrained_weights/HoloPart` resolve inside the HoloPart repo.

## Environment Probe

The configured local HoloPart environment is:

```text
/home/rui/miniconda3/envs/holopart/bin/python
```

Probe result:

```text
cuda_available True
torch 2.1.0+cu121
diffusers True
huggingface_hub True
torch_cluster True
pymeshlab True
trimesh True
diso True
```

So Phase 6 can plan for a real GPU inference attempt.

## Weight Download And Mirror

The upstream script downloads weights with:

```python
snapshot_download(repo_id="VAST-AI/HoloPart", local_dir="pretrained_weights/HoloPart")
```

The runner should set:

```text
HF_ENDPOINT=https://hf-mirror.com
```

This should be configurable through the HoloPart tool settings, with `hf_endpoint` defaulting to the mirror.

Because the upstream script hardcodes the relative weight directory, the runner should initially run from the HoloPart repo and let the script write/reuse:

```text
third_party/HoloPart/pretrained_weights/HoloPart
```

## Runner Design

Follow the existing `Sampart3DRunner` pattern:

- `HoloPartRunner` in `src/partpipeline/runners/holopart.py`
- `SubprocessRunner` handles stdout/stderr logs
- `HoloPartPreflightError` for missing inputs/env/script
- `HoloPartExecutionError` for nonzero exit or missing `output.glb`
- result dataclasses in `types.py`
- manifest update via orchestrator

## Risks

- The first real HoloPart run may spend time downloading weights.
- HoloPart may fail on GPU memory, especially with 34 parts and default `batch_size=8`.
- If default inference is too heavy, execution should capture logs and the next fix should lower `batch_size` or expose it as a CLI/config override.
- Network access to HuggingFace may fail without the mirror; `HF_ENDPOINT` must be present in the subprocess environment.

## Recommendation

Implement a single-run HoloPart command:

```bash
partpipeline holopart <run_dir>
```

The command should:

1. Require `bridge/prepared_parts.glb`.
2. Run upstream HoloPart script in the `holopart` environment.
3. Write logs to `run_dir/logs`.
4. Expect `run_dir/holopart/output.glb`.
5. Update manifest status to `holopart_complete`.
6. Preserve existing `sampart3d` and `bridge` manifest sections.

# Phase 6 Context: HoloPart Integration

## Phase Goal

Run HoloPart on the prepared multipart GLB produced by Phase 5 and collect the completed part output.

## Locked Decisions

### Phase Boundary

Phase 6 starts from an existing `bridge_complete` run.

Input:

```text
outputs/runs/<run>/bridge/prepared_parts.glb
```

Output:

```text
outputs/runs/<run>/holopart/output.glb
outputs/runs/<run>/logs/holopart.stdout.log
outputs/runs/<run>/logs/holopart.stderr.log
```

Phase 6 does not own SAMPart3D segmentation, bridge conversion, batch orchestration, or server batch mode. Those are already completed or reserved for other phases.

### Invocation Strategy

Use HoloPart's existing inference entrypoint first:

```text
third_party/HoloPart/scripts/inference_holopart.py
```

PartPipeline should wrap it through a layered runner/subprocess contract instead of modifying HoloPart source code unless planning finds a hard blocker.

### CLI Shape

Add a single-run command for an existing run directory:

```bash
partpipeline holopart <run_dir>
```

This command should require `bridge/prepared_parts.glb` to exist and should fail clearly if the run is not ready.

### Default HoloPart Parameters

Use HoloPart defaults for v1:

```text
seed = 42
num_inference_steps = 50
guidance_scale = 3.5
batch_size = 8
```

Expose these through config and/or CLI overrides where straightforward, but default behavior should match upstream HoloPart.

### Weight Download And Mirror

Allow automatic HoloPart weight download/reuse for Phase 6, but make the weight directory configurable.

The runner should set HuggingFace mirror support by default:

```text
HF_ENDPOINT=https://hf-mirror.com
```

This is required because the user asked to "open hg mirror", interpreted as using the HF/HuggingFace mirror for model weight download. The implementation should keep the value configurable so server runs can override it.

### Failure Handling

HoloPart failures must be surfaced through:

- subprocess exit code
- stdout/stderr log paths
- `manifest.json`

Failure manifest shape should include:

```text
error.type = "holopart"
error.message
error.issues or command/log references when available
```

The runner should treat missing `output.glb` after a zero exit code as a failure.

## Validation Expectations

Phase 6 should validate:

1. PartPipeline invokes HoloPart for `bridge/prepared_parts.glb`.
2. HoloPart writes `output.glb`.
3. The output is copied or written under `outputs/runs/<run>/holopart/output.glb`.
4. `manifest.json` records HoloPart output paths and status.
5. Failure cases produce helpful errors and log paths.

## Open Technical Questions For Planning

- Whether to call HoloPart through `python -m scripts.inference_holopart` or direct script path.
- Whether the current `holopart` conda environment can run full inference without additional CUDA/library fixes.
- Whether HoloPart's default output directory behavior should write directly to `run_dir/holopart` or to a temp folder followed by copy.
- Whether model weight path should be passed by changing upstream script arguments or by running from the HoloPart repo with configured environment variables.

## Out Of Scope

- Batch HoloPart execution.
- Server orchestration.
- Changing HoloPart model architecture or inference internals.
- Presentation reports or per-part export packaging beyond collecting `output.glb`.

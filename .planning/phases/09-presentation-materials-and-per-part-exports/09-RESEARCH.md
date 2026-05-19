---
phase: 9
type: research
status: complete
created: 2026-05-19
---

# Phase 9 Research: Exploded Assembly Presentation Video

## Goal

Phase 9 must turn a Phase 8 Level A presentation package into a clear MP4 animation: parts begin assembled, slide outward from the model center with slight rotation, pause for inspection, then return to their assembled positions. It also needs per-part GLB exports and optional batch animation generation.

## Environment Findings

Checked on WSL in `/home/rui/of_work/code/PartPipeline` using the `part` conda environment.

Available:

- `trimesh`
- `numpy`
- `PIL`
- `cv2`
- `matplotlib`

Not available in PATH / environment:

- `blender`
- `ffmpeg`
- `xvfb-run`
- `imageio`
- `moviepy`
- `pyrender`

OpenCV MP4 writing was tested with `cv2.VideoWriter_fourcc(*"mp4v")`; it opened successfully and wrote a valid small MP4 to `/tmp/partpipeline_cv2_test.mp4`.

## Real Asset Structure

Real Phase 8 package inspected:

```text
outputs/presentation/02.-01-20260518-190552/level_a_segmented_parts.glb
```

Findings:

- file exists
- size: 13,923,816 bytes
- loaded by `trimesh.load(..., force="scene")`
- object type: `trimesh.Scene`
- geometry count: `5`
- geometry names:
  - `part_000_label_0`
  - `part_001_label_1`
  - `part_002_label_2`
  - `part_003_label_3`
  - `part_004_label_4`

This is well-suited to per-part export and per-geometry animation. The source Level A scene already contains multiple named geometries.

## Recommended Rendering Approach

Use a pure Python renderer for Phase 9:

- `trimesh` to load `level_a_segmented_parts.glb`
- `trimesh` to export each geometry as `parts/part_001.glb`, etc.
- `numpy` to compute part centroids, model center, outward vectors, transforms, easing, and slight rotations
- `matplotlib` 3D axes with a fixed three-quarter view to render frames
- `PIL` or direct matplotlib canvas extraction to get RGB frames
- `cv2.VideoWriter` to encode MP4 with `mp4v`

This avoids installing Blender or ffmpeg for the first implementation while still producing a real MP4.

## Animation Design

Default parameters should be conservative and fast:

- fixed 3/4 view, for example `elev=25`, `azim=-45`
- 24 FPS
- 4 seconds total, or similar
- phases:
  - assembled start
  - explode outward
  - hold exploded state
  - return assembled
- outward distance based on scene diagonal and each part direction from the model center
- slight rotation around a deterministic axis for each part, scaled by explode progress
- final frame should return all transforms to the original assembled positions

## Code Integration

Add a new module:

```text
src/partpipeline/animation.py
```

Keep it separate from `presentation.py` so Phase 8 packaging stays simple. `presentation.py` can call animation generation when batch animation is requested, or CLI commands can call the animation module directly.

Likely functions:

```python
def export_parts(package_dir: Path) -> PartExportManifest: ...

def render_exploded_animation(
    package_dir: Path,
    duration_seconds: float = 4.0,
    fps: int = 24,
    width: int = 1280,
    height: int = 720,
) -> AnimationManifest: ...
```

Add CLI:

```text
partpipeline animate <package_dir>
```

Add optional batch behavior:

```text
partpipeline package-batch <batch_manifest> --generate-animation
```

or an equivalent explicit option. It must not render videos by default.

## Risks And Controls

- **Matplotlib rendering quality:** This is good enough for first MP4 demos, but not as polished as Blender. Keep advanced rendering deferred.
- **Encoding availability:** OpenCV MP4 was verified locally, but the implementation should fail clearly if `VideoWriter` cannot open.
- **Large/complex models:** Use defaults that work for the current real asset and expose resolution/FPS/duration options so expensive renders can be tuned.
- **Geometry transforms:** Preserve original assembled transforms and write tests that verify final transform returns to assembled positions.
- **Batch cost:** Keep batch animation opt-in because rendering per item can take time.

## Verification Strategy

Unit tests should use small synthetic `trimesh.Scene` assets:

- part export writes `parts/part_001.glb`, etc.
- animation manifest includes source package, part count, duration, FPS, frame count, and MP4 path
- MP4 file is non-empty
- missing Level A fails clearly
- batch animation option records animation paths only when enabled

Real smoke test:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli animate outputs/presentation/02.-01-20260518-190552
```

Expected outputs:

```text
outputs/presentation/02.-01-20260518-190552/parts/part_001.glb
outputs/presentation/02.-01-20260518-190552/animation/exploded_assembly.mp4
outputs/presentation/02.-01-20260518-190552/animation/animation_manifest.json
```


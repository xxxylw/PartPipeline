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

Available in the current `part` environment before installing additional rendering tools:

- `trimesh`
- `numpy`
- `PIL`
- `cv2`
- `matplotlib`

Not available in PATH / environment during the initial probe:

- `blender`
- `ffmpeg`
- `xvfb-run`
- `imageio`
- `moviepy`
- `pyrender`

OpenCV MP4 writing was tested with `cv2.VideoWriter_fourcc(*"mp4v")`; it opened successfully and wrote a valid small MP4 to `/tmp/partpipeline_cv2_test.mp4`.

## Updated Rendering Decision

After the initial research, the user chose to use Blender and ffmpeg instead of the pure Python/OpenCV rendering path. Blender/ffmpeg should be installed in or exposed through the `part` conda environment.

The planning direction is therefore:

- use Python/`trimesh` for lightweight metadata and part export where useful
- use Blender CLI for scene setup, camera, lighting, part motion, and frame/video rendering
- use ffmpeg for final MP4 encoding if Blender renders image frames rather than directly writing MP4
- add preflight checks that resolve Blender and ffmpeg from the `part` environment and fail clearly when unavailable
- keep the OpenCV approach as a documented fallback only, not as the primary implementation

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

Use Blender/ffmpeg for Phase 9:

- `trimesh` can still inspect `level_a_segmented_parts.glb` and export individual part GLBs
- Blender CLI should import the Level A GLB or the exported parts
- Blender should compute/receive part origins, model center, outward vectors, keyframes, slight rotation, camera, and lighting
- Blender can render frames to `animation/frames/`
- ffmpeg should encode frames into `animation/exploded_assembly.mp4`

This should produce a more polished, reliable 3D presentation video than the Python/matplotlib renderer. It does add an environment requirement, so Phase 9 must include preflight and setup guidance for the `part` environment.

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

def preflight_animation_tools(...) -> AnimationToolStatus: ...

def render_exploded_animation(
    package_dir: Path,
    duration_seconds: float = 4.0,
    fps: int = 24,
    width: int = 1280,
    height: int = 720,
) -> AnimationManifest: ...
```

Add a Blender helper script, for example:

```text
scripts/render_exploded_assembly.py
```

The CLI can call:

```text
blender --background --python scripts/render_exploded_assembly.py -- <args>
ffmpeg -framerate ... -i frames/%04d.png ... exploded_assembly.mp4
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

- **Environment availability:** Blender and ffmpeg were not present in the initial PATH probe. Implementation must preflight these tools and document/install them in the `part` environment.
- **Renderer invocation:** Blender CLI arguments and Python script invocation must be deterministic and logged.
- **Encoding availability:** ffmpeg must be checked before rendering, or Blender must be configured to produce the final MP4 directly.
- **Large/complex models:** Use defaults that work for the current real asset and expose resolution/FPS/duration options so expensive renders can be tuned.
- **Geometry transforms:** Preserve original assembled transforms and write tests that verify final transform returns to assembled positions.
- **Batch cost:** Keep batch animation opt-in because rendering per item can take time.

## Verification Strategy

Unit tests should use small synthetic `trimesh.Scene` assets:

- part export writes `parts/part_001.glb`, etc.
- animation manifest includes source package, part count, duration, FPS, frame count, and MP4 path
- Blender/ffmpeg preflight reports tool paths or clear missing-tool errors
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

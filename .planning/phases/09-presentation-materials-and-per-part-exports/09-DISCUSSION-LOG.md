# Phase 9: Exploded Assembly Presentation Video - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-19
**Phase:** 9-Exploded Assembly Presentation Video
**Areas discussed:** Output format, animation style, camera view, part exports, batch behavior

---

## Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| Real MP4 video | Produce a video file suitable for direct demo/report use. | yes |
| HTML/Three.js animation | Produce a browser-playable interactive or scripted animation. | |
| Both by default | Produce both a page and video in the same phase. | |

**User's choice:** Real MP4 video.
**Notes:** The user wants a clear video presentation of the segmentation result.

---

## Animation Style

| Option | Description | Selected |
|--------|-------------|----------|
| Straight slide out/in | Parts move outward from center and return without rotation. | |
| Slide with slight rotation | Parts slide outward while rotating subtly for a more presentable effect. | yes |
| Sequential part reveal | Parts move one by one before returning. | |

**User's choice:** Slide with slight rotation.
**Notes:** The user explicitly wanted the outward motion to have a little rotation so the result is more visually demonstrative.

---

## Camera View

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed three-quarter view | Keep the camera stable at a 3/4 view. | yes |
| Camera orbit | Move the camera around the model while parts animate. | |
| Multiple cuts | Render several views or angles. | |

**User's choice:** Fixed three-quarter view.
**Notes:** Fixed view should keep the animation easy to understand and simpler to render reliably.

---

## Part Exports

| Option | Description | Selected |
|--------|-------------|----------|
| Use geometry in place only | Animate Level A geometries without writing separate part files. | |
| Export individual parts | Write `parts/part_001.glb`, `parts/part_002.glb`, etc. | yes |
| Export only on request | Make part export optional. | |

**User's choice:** Export individual parts.
**Notes:** The user wants separate part files alongside the animation output.

---

## Batch Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Always animate batch items | Every batch package generates video. | |
| Optional batch animation | Batch generation supports animation as an explicit option. | yes |
| Single package only | Do not support batch animation in this phase. | |

**User's choice:** Optional batch animation.
**Notes:** Batch item animation should exist, but it should be opt-in because rendering videos can be expensive.

---

## Agent Discretion

- Renderer/backend is now locked to Blender CLI plus ffmpeg, installed or available through the `part` conda environment.
- Exact FPS, duration, easing, rotation angle, lighting, and output filenames may be chosen during planning.
- CLI naming can follow existing project conventions.

## Deferred Ideas

- Interactive web viewer controls.
- Camera orbit.
- Advanced rendering/material styling.
- Automatic quality scoring.

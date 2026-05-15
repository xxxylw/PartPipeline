# State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-15)

**Core value:** A user can provide one `.glb` or a folder of `.glb` files and receive organized, presentation-ready segmented and completed part outputs.
**Current focus:** Phase 4 - SAMPart3D Integration

## Last Session

Implemented the PartPipeline-side SAMPart3D runner for Phase 4. Automated tests pass and dry-run works with the real SAMPart3D command contract. Real model execution is currently blocked by missing local SAMPart3D prerequisites: Blender at `third_party/SAMPart3D/blender-4.0.0-linux-x64/blender` and backbone weight at `third_party/SAMPart3D/ckpt/ptv3-object.pth`.

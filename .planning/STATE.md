# State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-05-15)

**Core value:** A user can provide one `.glb` or a folder of `.glb` files and receive organized, presentation-ready segmented and completed part outputs.
**Current focus:** Phase 5 - Segmentation Bridge Converter

## Last Session

Completed Phase 4 SAMPart3D integration. A real run on `/mnt/d/of_work/resources/Disassembled parts/08.Toulouse 双人沙发组合.glb` completed with status `sampart3d_complete`, produced the original result at `third_party/SAMPart3D/exp/sampart3d/08.toulouse-20260515-160213/results/5000/mesh_1.0.npy`, and copied it to `outputs/runs/08.toulouse-20260515-160213/sam/mesh_1.0.npy`. Next: convert the source GLB plus SAMPart3D mask into a HoloPart-compatible multipart GLB.

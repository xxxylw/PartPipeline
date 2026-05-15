# PartPipeline

PartPipeline orchestrates a GLB-to-parts workflow:

1. Run SAMPart3D on an input `.glb`.
2. Use the selected face mask, default `mesh_1.0.npy`, to create a multipart GLB scene.
3. Run HoloPart on that multipart scene.
4. Save complete outputs for inspection, presentation, and downstream use.

## Planned CLI

```bash
partpipeline run path/to/model.glb
partpipeline batch path/to/glb_directory
```

Phase 1 provides the repository scaffold and dependency wiring. Model execution lands in later phases.

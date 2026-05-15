# Requirements

## v1 Requirements

### Repository

- [ ] **REPO-01**: Developer can clone/open PartPipeline as a standalone project under `/home/rui/of_work/code/PartPipeline`.
- [ ] **REPO-02**: Developer can update SAMPart3D and HoloPart through fork-backed submodules.

### Pipeline Commands

- [ ] **CLI-01**: User can run a single `.glb` through one command.
- [ ] **CLI-02**: User can run all `.glb` files in a directory through one batch command.
- [x] **CLI-03**: User can override the SAMPart3D mask scale, with `1.0` as the default. Validated for SAMPart3D result selection in Phase 4.

### Segmentation Bridge

- [x] **BRIDGE-01**: System can locate SAMPart3D output `mesh_1.0.npy` for an input object. Validated in Phase 4.
- [x] **BRIDGE-02**: System can convert `input.glb + mesh_1.0.npy` into a HoloPart-compatible multipart GLB scene. Validated in Phase 5.

### Completion

- [ ] **HOLO-01**: System can pass the prepared multipart GLB to HoloPart and collect `output.glb`.

### Outputs

- [ ] **OUT-01**: Each run writes a manifest JSON with input path, selected mask, intermediate paths, final output path, status, and timings.
- [ ] **OUT-02**: Each run preserves useful presentation artifacts: SAM mask, prepared multipart GLB, HoloPart output, logs, and per-part exports where practical.

### Environment

- [x] **ENV-01**: System documents whether a shared environment works or whether env dispatch is required. Validated in Phase 2.
- [x] **ENV-02**: User-facing commands remain unified even if internal steps use separate conda environments. Validated in Phase 2.

## v2 Requirements

- [ ] Auto-select the best SAMPart3D scale based on part count or quality heuristics.
- [ ] Generate visual previews or an HTML report for presentation.
- [ ] Add resumable batch runs with retry controls.

## Out of Scope

- Model training.
- Web UI.
- Cloud execution.
- Storing model weights in git.

## Traceability

| Requirement | Phase |
|-------------|-------|
| REPO-01 | Phase 1 |
| REPO-02 | Phase 1 |
| CLI-01 | Phase 1, Phase 3, Phase 4 |
| CLI-02 | Phase 1, Phase 3, Phase 7 |
| CLI-03 | Phase 1, Phase 3, Phase 4 |
| BRIDGE-01 | Phase 4 |
| BRIDGE-02 | Phase 5 |
| HOLO-01 | Phase 6 |
| OUT-01 | Phase 3, Phase 4, Phase 7 |
| OUT-02 | Phase 7 |
| ENV-01 | Phase 2 |
| ENV-02 | Phase 2 |

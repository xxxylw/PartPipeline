# Roadmap

### Phase 1: Project Scaffold and Repository Wiring
**Goal:** Create the PartPipeline project shell, planning docs, CLI outline, and fork-backed submodule dependencies.
**Mode:** mvp
**Requirements:** REPO-01, REPO-02, CLI-01, CLI-02, CLI-03
**Success Criteria**:
1. `/home/rui/of_work/code/PartPipeline` exists as a git repo with planning docs.
2. `third_party/SAMPart3D` and `third_party/HoloPart` point to the user forks.
3. A minimal `partpipeline run` and `partpipeline batch` CLI outline exists.
4. Generated outputs are excluded from git while output structure is documented.

### Phase 2: Environment Strategy
**Goal:** Determine whether one conda environment can run both model projects; if not, implement a dispatcher plan.
**Status:** Complete (2026-05-15)
**Mode:** mvp
**Requirements:** ENV-01, ENV-02
**Success Criteria**:
1. Dependency compatibility is tested against SAMPart3D and HoloPart imports.
2. The selected environment strategy is documented.
3. The user-facing command remains a single PartPipeline command.

### Phase 3: Runtime Configuration and Layered Core
**Goal:** Build the profile-based configuration, layered runtime core, artifact layout, and manifest/runner contracts without executing model pipelines.
**Status:** Complete (2026-05-15)
**Mode:** mvp
**Requirements:** CLI-01, CLI-02, CLI-03, OUT-01, ENV-02
**Success Criteria**:
1. `local_wsl` and `server` YAML profiles exist, with server SSH identity recorded and filesystem paths templated.
2. CLI commands load config/profile data through a config layer instead of hardcoded paths.
3. Run artifact directories and `manifest.json` can be created without model execution.
4. Subprocess runner contracts record command, cwd, env, exit code, and log paths.
5. Code is separated into simple CLI, config, orchestration, runner, artifacts, and types layers.

### Phase 4: SAMPart3D Integration
**Goal:** Run SAMPart3D for a single input `.glb` through the layered runner and locate the default `mesh_1.0.npy` segmentation result.
**Mode:** mvp
**Requirements:** CLI-01, CLI-03, BRIDGE-01
**Success Criteria**:
1. A single input GLB can trigger SAMPart3D through PartPipeline.
2. The run records render, train, eval, and result paths.
3. `mesh_1.0.npy` is selected by default and can be overridden.
4. The SAMPart3D subprocess uses config/profile values and fixes required CUDA loader paths.

### Phase 5: Segmentation Bridge Converter
**Goal:** Convert a SAMPart3D face mask and source GLB into HoloPart multipart GLB input.
**Mode:** mvp
**Requirements:** BRIDGE-01, BRIDGE-02
**Success Criteria**:
1. The converter validates face-count compatibility.
2. Each part id becomes a separate geometry in the output scene.
3. The prepared GLB can be loaded by HoloPart `prepare_data`.

### Phase 6: HoloPart Integration
**Goal:** Run HoloPart on prepared multipart GLB input and collect completed part output.
**Mode:** mvp
**Requirements:** HOLO-01
**Success Criteria**:
1. PartPipeline invokes HoloPart for a prepared GLB.
2. The final `output.glb` is copied into the run output folder.
3. Failures surface clear error messages and log paths.

### Phase 7: Batch, Server Run Mode, and Presentation Outputs
**Goal:** Support folder-level batch processing, server-friendly runs, and complete artifacts for review and presentation.
**Mode:** mvp
**Requirements:** CLI-02, OUT-01, OUT-02
**Success Criteria**:
1. A directory of `.glb` files can be queued and processed.
2. Each asset has a manifest with status, paths, and timings.
3. Outputs include masks, prepared GLB, completed GLB, logs, and optional per-part exports.
4. Server profile usage is documented for host `d5`.

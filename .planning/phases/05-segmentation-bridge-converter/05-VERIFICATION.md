# Phase 5 Verification: Segmentation Bridge Converter

## Verdict

PASS.

## Automated Tests

Command:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
```

Result:

```text
Ran 26 tests in 0.172s
OK
```

## Real Artifact Validation

Command:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli bridge outputs/runs/08.toulouse-20260515-160213
```

Result:

```text
Status: bridge_complete
Prepared GLB: outputs/runs/08.toulouse-20260515-160213/bridge/prepared_parts.glb
Part manifest: outputs/runs/08.toulouse-20260515-160213/bridge/part_manifest.json
```

Trimesh load check:

```text
geometry_count 34
original_part_count 34
final_part_count 34
merge_count 0
merged_unique 34
prepared_size 42247284
```

HoloPart prepare-data smoke:

```text
part_count 34
whole_cond_shape (34, 20480, 7)
part_cond_shape (34, 20480, 6)
```

## Requirement Coverage

- BRIDGE-02: satisfied. `input.glb + mesh_1.0.npy` now converts into a HoloPart-compatible multipart GLB.

## Notes

The bridge command preserves existing manifest content and adds a `bridge` section. For the real run, a minimal `sampart3d` section was reconstructed because an earlier bridge attempt had overwritten that section before the preservation fix.

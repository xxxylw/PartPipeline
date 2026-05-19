# Phase 8 Verification

## Unit Tests

Targeted Phase 8 tests:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest tests.test_presentation tests.test_cli
```

Result:

```text
Ran 16 tests
OK
```

Full project suite:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover tests
```

Result:

```text
Ran 50 tests
OK
```

Diff whitespace check:

```bash
git diff --check
```

Result: passed.

## Real Run Smoke Test

Command:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli package outputs/runs/02.-01-20260518-190552
```

Output:

```text
Package directory: /home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552
Manifest: /home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552/presentation_manifest.json
Default level: A
```

Generated files:

```text
outputs/presentation/02.-01-20260518-190552/level_a_segmented_parts.glb
outputs/presentation/02.-01-20260518-190552/part_manifest.json
outputs/presentation/02.-01-20260518-190552/presentation_manifest.json
```

Manifest checks:

- `default_level` is `A`.
- Level A package path is `level_a_segmented_parts.glb`.
- Level A has `recommended_for_display: true`.
- Level B is absent by default.
- Original input path is recorded.
- Original GLB is not copied by default.

## Real Batch Smoke Test

Command:

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli package-batch outputs/runs/batches/batch-20260518-190552/batch_manifest.json
```

Output:

```text
Presentation directory: /home/rui/of_work/code/PartPipeline/outputs/presentation
Batch presentation manifest: /home/rui/of_work/code/PartPipeline/outputs/presentation/presentation_batch_manifest.json
Total: 1
Packaged: 1
Failed: 0
```

## Acceptance Criteria

- Completed run packaging: passed.
- Level A default/recommended behavior: passed.
- Level B explicit opt-in behavior: covered by unit tests.
- Batch manifest packaging: covered by unit tests.
- Presentation manifest contract: passed.

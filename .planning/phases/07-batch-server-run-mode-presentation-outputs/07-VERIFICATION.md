# Phase 7 Verification

## 验证结论

Phase 7 的代码级验证通过。PartPipeline 现在可以 staging 一组 GLB 到 `inputs/phase7`，并对该目录运行 `batch --dry-run` 生成批次 manifest。真实模型批处理入口已经接好，但本次验证没有启动真实长耗时模型批处理。

## 自动化测试

命令：

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
```

结果：

```text
Ran 39 tests in 0.693s
OK
```

覆盖点：

- `stage_glb_inputs` 复制 `.glb`，忽略非 GLB，写 `input_manifest.json`。
- 文件名包含中文和空格时 staging/manifest 能保留路径。
- `BatchManifest` 写出 `total`、`succeeded`、`failed` 和 `items`。
- `run_batch_pipeline` 支持 success、failure、continue-on-error、dry-run、empty input。
- CLI 支持 `stage-inputs` 和真实 `batch` 命令。

## 输入 staging 验证

命令：

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli stage-inputs \
  /mnt/c/Users/qirui.huang/Downloads/assets/gt_glbs \
  --destination inputs/phase7 \
  --limit 3
```

结果：

```text
Source: /mnt/c/Users/qirui.huang/Downloads/assets/gt_glbs
Destination: /home/rui/of_work/code/PartPipeline/inputs/phase7
GLB count: 3
Input manifest: /home/rui/of_work/code/PartPipeline/inputs/phase7/input_manifest.json
```

说明：当前 staging 按文件名排序后取前 3 个 GLB，因此本次样本为：

```text
02.香叶天竺葵01.glb
03.一球悬铃木 07.glb
04.紫花风铃木 02.glb
```

## Batch dry-run 验证

命令：

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli batch inputs/phase7 --dry-run --limit 2
```

结果：

```text
Profile: local_wsl
Status: dry_run
Total: 2
Succeeded: 0
Failed: 0
Batch manifest: /home/rui/of_work/code/PartPipeline/outputs/runs/batches/batch-20260518-185913/batch_manifest.json
```

batch manifest 中每个 item 记录了：

- `asset_name`
- `input_path`
- `source_path`
- `run_dir`
- `manifest_path`
- `status`
- `error`

## CLI help 验证

确认 `stage-inputs` 包含：

```text
--destination
```

确认 `batch` 包含：

```text
--limit
--stop-on-error
--skip-holopart
```

## Git 忽略验证

`git status --short --ignored` 显示：

```text
!! inputs/
!! outputs/runs/
```

说明生成输入和输出没有被加入 git。

## 真实长耗时验证

后续补充执行了真实模型批处理：

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli batch inputs/phase7 --limit 1
```

结果：

```text
Profile: local_wsl
Status: complete
Total: 1
Succeeded: 1
Failed: 0
Batch manifest: /home/rui/of_work/code/PartPipeline/outputs/runs/batches/batch-20260518-190552/batch_manifest.json
```

真实样本：

```text
asset_name=02.香叶天竺葵01.glb
run_dir=/home/rui/of_work/code/PartPipeline/outputs/runs/02.-01-20260518-190552
item_status=holopart_complete
run_status=holopart_complete
```

最终 HoloPart 输出：

```text
output_glb=/home/rui/of_work/code/PartPipeline/outputs/runs/02.-01-20260518-190552/holopart/output.glb
output_size=1054224
loaded_type=Scene
geometry_count=5
```

说明：`output.glb` 已用 `trimesh.load(..., force="scene")` 验证可加载。该真实批处理运行启动了 SAMPart3D、bridge 和 HoloPart，最终 batch 状态为 `complete`。

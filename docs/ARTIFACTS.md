# 产物说明

PartPipeline 的关键设计之一是所有阶段都写结构化产物，方便检查、恢复和批处理汇总。

## input_manifest.json

`stage-inputs` 会写：

- `input_manifest.json`

每个 item 记录：

- 原始路径
- staged 路径
- asset name
- 文件大小

## 单个 run 目录

run 目录位于配置里的 `output_root` 下，通常形如：

```text
outputs/runs/<asset-stem>-YYYYMMDD-HHMMSS/
```

内部结构：

```text
logs/
sam/
bridge/
prepared/
holopart/
manifest.json
```

## 命令记录

runner 会记录 subprocess 的：

- argv
- cwd
- exit code
- stdout log
- stderr log
- dry-run 标记
- 关键环境变量

这些信息会写入 run manifest，方便失败后手动复现。

## SAMPart3D 产物

SAMPart3D 会在自己的 experiment 目录下产生多个尺度的 mask。PartPipeline 会把选定 mask 拷贝到 run 的 `sam/` 下。

常见 mask：

- `mesh_0.0.npy`
- `mesh_0.5.npy`
- `mesh_1.0.npy`
- `mesh_1.5.npy`
- `mesh_2.0.npy`

默认使用 `mesh_1.0.npy`。

## Bridge 产物

Bridge 阶段写：

- `bridge/prepared_parts.glb`
- `bridge/mesh_<scale>_merged.npy`
- `bridge/part_manifest.json`

`part_manifest.json` 记录：

- source GLB
- source mask
- 原始 part 数量
- 合并后的 part 数量
- 每个 part 的 label、名称、面数、面积、比例
- 小碎片 merge history
- face count 校验结果

## HoloPart 产物

HoloPart 成功后应写：

- `holopart/output.glb`

这个结果在展示包里属于 Level B，只作为可选对比结果。

## Batch 产物

批处理写：

```text
outputs/runs/batches/<batch-id>/batch_manifest.json
```

它记录：

- 总资产数
- 成功数
- 失败数
- 每个资产的 run 目录
- 每个资产的 manifest 路径
- 错误类型和错误消息

## Presentation 产物

展示包包含：

- `level_a_segmented_parts.glb`
- 可选 `level_b_holopart_output.glb`
- 可选 `original.glb`
- 可选 `part_manifest.json`
- `presentation_manifest.json`

Level A 是默认推荐展示结果。

## Animation 产物

动画阶段包含：

- `parts/part_001.glb`、`parts/part_002.glb` 等单件 GLB
- `parts/parts_manifest.json`
- `preview/segmented_front.png`
- `preview/exploded_view.png`
- `animation/blender_job.json`
- `animation/frames/frame_0001.png` 等帧
- `animation/exploded_assembly.mp4`
- `animation/animation_manifest.json`

注意：`parts/part_*.glb` 是为了动画和单件检查从 Level A 中导出的单独 geometry；主展示结果仍以 `level_a_segmented_parts.glb` 为准。

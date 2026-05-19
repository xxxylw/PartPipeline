# Phase 9 Summary: Exploded Assembly Presentation Video

## 做了什么

Phase 9 把 Phase 8 的 Level A 展示包继续加工成更适合汇报的材料。输入仍然是 `level_a_segmented_parts.glb`，不会重新跑 SAMPart3D、bridge 或 HoloPart。

新增能力：

- 导出单独零件：`parts/part_001.glb`、`parts/part_002.glb` 等。
- 写出零件清单：`parts/parts_manifest.json`，记录来源 geometry、路径、中心点、包围盒、顶点数和面数。
- 生成真实 MP4：`animation/exploded_assembly.mp4`。
- 写出动画清单：`animation/animation_manifest.json`，记录视频参数、工具路径、命令和输出位置。
- 新增 CLI：`partpipeline animate <package_dir>`。
- `package-batch` 新增显式可选项：`--generate-animation`，默认不会批量渲染，避免误触发耗时任务。

## 动画设计

动画固定使用 3/4 视角。每个 part 从组装状态开始，向模型中心外侧滑开，同时带轻微旋转；中间短暂停留，然后回到原始组装位置。最终帧与 Level A 的原始排布一致。

渲染链路是 Blender + ffmpeg：

- Blender 负责导入 Level A GLB、设置 camera/light/keyframes，并输出 PNG 帧。
- ffmpeg 负责把 `animation/frames/frame_0001.png...` 合成为 `exploded_assembly.mp4`。
- WSL headless 环境里默认实时渲染后端会碰到 EGL/GLX 问题，所以脚本使用 CPU Cycles 渲染，服务器上也更稳。

## 常用命令

从源码运行：

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli animate outputs/presentation/02.-01-20260518-190552
```

轻量测试参数：

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli animate \
  outputs/presentation/02.-01-20260518-190552 \
  --duration-seconds 2 \
  --fps 12 \
  --width 640 \
  --height 360
```

批处理展示包时可选生成动画：

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli package-batch \
  outputs/runs/batches/<batch-id>/batch_manifest.json \
  --generate-animation
```

## 默认参数

默认配置写在 `configs/default.yaml` 的 `pipeline.animation`：

- `blender`: `/home/rui/miniconda3/envs/part/bin/blender`
- `ffmpeg`: `/home/rui/miniconda3/envs/part/bin/ffmpeg`
- `duration_seconds`: 4.0
- `fps`: 24
- `width`: 1280
- `height`: 720
- `explode_scale`: 1.25
- `rotation_degrees`: 15.0

这些参数都可以通过 CLI 覆盖。

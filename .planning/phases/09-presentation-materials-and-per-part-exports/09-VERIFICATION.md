# Phase 9 Verification

## 环境检查

ffmpeg 已安装在 `part` 环境：

```text
ffmpeg version 8.0.1
```

Blender 使用官方 Linux x64 tarball 安装并链接到 `part` 环境：

```text
/home/rui/miniconda3/envs/part/bin/blender
Blender 4.5.0
build date: 2025-07-15
```

## 测试

目标测试：

```bash
cd /home/rui/of_work/code/PartPipeline
/home/rui/miniconda3/bin/conda run -n part python -m unittest tests.test_animation tests.test_presentation tests.test_cli
```

结果：

```text
Ran 24 tests in 0.281s
OK
```

完整测试：

```bash
cd /home/rui/of_work/code/PartPipeline
/home/rui/miniconda3/bin/conda run -n part python -m unittest discover -s tests
```

结果：

```text
Ran 58 tests in 0.309s
OK
```

说明：`part` 环境没有安装 pytest，所以验证使用 Python 标准库 `unittest`。

## 真实展示包烟测

输入展示包：

```text
/home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552
```

执行命令：

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/bin/conda run -n part python -m partpipeline.cli animate \
  outputs/presentation/02.-01-20260518-190552 \
  --duration-seconds 2 \
  --fps 12 \
  --width 640 \
  --height 360
```

输出：

```text
Package directory: /home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552
Parts manifest: /home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552/parts/parts_manifest.json
Video: /home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552/animation/exploded_assembly.mp4
Animation manifest: /home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552/animation/animation_manifest.json
```

产物检查：

```text
part GLB count: 5
video width: 640
video height: 360
duration: 2.000000
frames: 24
```

关键文件：

```text
/home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552/parts/part_001.glb
/home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552/parts/parts_manifest.json
/home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552/animation/exploded_assembly.mp4
/home/rui/of_work/code/PartPipeline/outputs/presentation/02.-01-20260518-190552/animation/animation_manifest.json
```

## 结论

Phase 9 的核心目标已达成：Level A 展示包可以导出 per-part GLB，并生成真实 exploded/reassembled MP4。Batch 动画生成保持显式 opt-in。

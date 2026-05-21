# 架构说明

PartPipeline 是一个分层的 Python CLI。它不直接实现 SAMPart3D 或 HoloPart 的模型逻辑，而是把这些外部工程作为 subprocess 工具调用，并围绕它们提供统一入口、路径管理、manifest、批处理、展示打包和动画生成。

## 核心职责

PartPipeline 负责：

- 管理输入 GLB 和输出目录。
- 调用 SAMPart3D 并记录命令、环境和日志。
- 选择指定分割尺度的 `mesh_<scale>.npy`。
- 把 face mask 转成 multipart GLB。
- 可选调用 HoloPart。
- 批量处理多个 GLB。
- 生成 presentation package。
- 生成爆炸装配动画。

PartPipeline 不负责：

- 训练或修改 SAMPart3D/HoloPart。
- 管理模型权重下载。
- 自动修复第三方环境依赖。
- 判断某个分割尺度在语义上是否一定正确。

## 模块分层

| 层 | 主要文件 | 职责 |
|----|----------|------|
| CLI | `src/partpipeline/cli.py` | 暴露 `stage-inputs`、`run`、`batch`、`bridge`、`holopart`、`package`、`package-batch`、`animate` 命令。 |
| 配置 | `src/partpipeline/config.py`、`configs/default.yaml` | 加载 YAML profile、解析路径、提供 pipeline 默认参数。 |
| 编排 | `src/partpipeline/orchestrator.py` | 串联单资产 run、已有 run 的 bridge/HoloPart、batch 处理和错误记录。 |
| Runner | `src/partpipeline/runners/` | 封装 SAMPart3D/HoloPart subprocess，做 preflight、环境变量、日志和命令记录。 |
| Bridge | `src/partpipeline/bridge.py` | 校验 face mask，把 label 切成 geometry，合并小碎片，导出 multipart GLB。 |
| 产物 | `src/partpipeline/artifacts.py` | 创建目录、写 run/batch/presentation/animation manifest。 |
| 展示 | `src/partpipeline/presentation.py` | 把 run 输出复制成 Level A/Level B 展示包。 |
| 动画 | `src/partpipeline/animation.py`、`scripts/render_exploded_assembly.py` | 导出单件 GLB，调用 Blender 渲染帧，再用 ffmpeg 编码 MP4。 |

## 数据流

```text
source .glb
  -> stage 到 run/sam/
  -> SAMPart3D
  -> mesh_<scale>.npy
  -> BridgeConverter
  -> bridge/prepared_parts.glb
  -> 可选 HoloPart
  -> presentation package
  -> 可选 exploded assembly animation
```

## Manifest 是阶段接口

项目大量依赖 JSON manifest 作为阶段之间的接口：

- `input_manifest.json`：记录原始输入和 staged 输入。
- `manifest.json`：记录单个 run 的状态、路径、命令、SAMPart3D、bridge、HoloPart 和错误信息。
- `batch_manifest.json`：记录批处理里的每个资产状态。
- `presentation_manifest.json`：记录展示包的 Level A/Level B 文件。
- `parts_manifest.json`：记录动画阶段导出的每个 part。
- `animation_manifest.json`：记录动画参数、工具路径、命令和输出视频。

## 分割尺度

SAMPart3D 实际输出多个尺度的 mask，例如：

- `mesh_0.0.npy`
- `mesh_0.5.npy`
- `mesh_1.0.npy`
- `mesh_1.5.npy`
- `mesh_2.0.npy`

PartPipeline 默认使用 `mesh_1.0.npy`。一般来说，尺度越小越细碎，尺度越大越粗合并；具体资产仍需人工检查。

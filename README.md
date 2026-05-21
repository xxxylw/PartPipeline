# PartPipeline

PartPipeline 是一个面向 3D 资产的 GLB 分件流水线。它用 SAMPart3D 对输入 `.glb` 做面级分割，再把选定的分割 mask 转换成 multipart GLB；需要时可以继续调用 HoloPart 做部件补全，并把结果打包成适合检查、汇报和动画展示的 presentation package。

## 流水线概览

```text
输入 .glb
  -> SAMPart3D 生成 mesh_<scale>.npy
  -> bridge 转成 bridge/prepared_parts.glb
  -> 可选 HoloPart 生成 holopart/output.glb
  -> package 生成展示包
  -> 可选 animate 生成爆炸装配视频
```

展示包默认推荐使用 Level A：

- `level_a_segmented_parts.glb`：bridge 阶段的分件结果，保留原始分割几何，是默认展示结果。
- `level_b_holopart_output.glb`：HoloPart 补全结果，只在显式请求时作为对比结果加入。

## 目录结构

- `src/partpipeline/cli.py`：Typer CLI 入口。
- `src/partpipeline/orchestrator.py`：单资产、已有 run、HoloPart、batch 的编排逻辑。
- `src/partpipeline/runners/`：SAMPart3D 和 HoloPart 的 subprocess runner。
- `src/partpipeline/bridge.py`：face mask 校验、小碎片合并、multipart GLB 导出。
- `src/partpipeline/presentation.py`：Level A/Level B 展示包打包。
- `src/partpipeline/animation.py`：单件 GLB 导出和 Blender/ffmpeg 动画生成。
- `scripts/render_exploded_assembly.py`：Blender 后台渲染脚本。
- `configs/default.yaml`：本地和服务器 profile。
- `docs/`：中文项目文档。
- `tests/`：配置、runner、编排、bridge、展示包、动画和 CLI 的单元测试。
- `third_party/SAMPart3D`、`third_party/HoloPart`：第三方模型工程子模块。

## 安装

在仓库根目录执行：

```bash
python -m pip install -e .
```

安装后会得到 `partpipeline` 命令：

```bash
partpipeline --help
```

完整模型运行还需要配置好的 SAMPart3D/HoloPart 环境、权重、Blender 和 ffmpeg。详见 [配置说明](docs/CONFIGURATION.md) 与 [环境与服务器](docs/ENVIRONMENT.md)。

## 常用命令

```bash
partpipeline stage-inputs /path/to/glbs --destination inputs/phase7
partpipeline run /path/to/model.glb --config configs/default.yaml
partpipeline batch inputs/phase7 --config configs/default.yaml
partpipeline bridge outputs/runs/<run-id> --config configs/default.yaml
partpipeline holopart outputs/runs/<run-id> --config configs/default.yaml
partpipeline package outputs/runs/<run-id> --presentation-dir outputs/presentation
partpipeline animate outputs/presentation/<package-id> --config configs/default.yaml
```

批量打包并生成动画：

```bash
partpipeline package-batch outputs/runs/batches/<batch-id>/batch_manifest.json \
  --presentation-dir outputs/presentation \
  --generate-animation
```

## 文档

- [文档索引](docs/README.md)
- [架构说明](docs/ARCHITECTURE.md)
- [使用指南](docs/USAGE.md)
- [配置说明](docs/CONFIGURATION.md)
- [产物说明](docs/ARTIFACTS.md)
- [环境与服务器](docs/ENVIRONMENT.md)

## 测试

```bash
python -m unittest discover tests
```

多数测试使用临时文件和 fake subprocess runner。完整模型推理需要真实第三方仓库、conda 环境、模型权重、Blender 和 ffmpeg。

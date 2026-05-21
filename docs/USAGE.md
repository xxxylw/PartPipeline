# 使用指南

## 安装

```bash
python -m pip install -e .
partpipeline --help
```

如果只跑单元测试，不一定需要真实模型环境。要跑完整链路，则需要配置好 SAMPart3D、HoloPart、模型权重、Blender 和 ffmpeg。

## 1. 准备输入

把目录里的 `.glb` 复制到 PartPipeline 管理的输入目录：

```bash
partpipeline stage-inputs /path/to/glb_directory --destination inputs/phase7
```

只取前几个文件做试跑：

```bash
partpipeline stage-inputs /path/to/glb_directory --destination inputs/phase7 --limit 3
```

## 2. 跑单个资产

```bash
partpipeline run /path/to/model.glb --config configs/default.yaml
```

指定 profile 和分割尺度：

```bash
partpipeline run /path/to/model.glb \
  --config configs/default.yaml \
  --profile local_wsl \
  --mask-scale 1.0
```

只生成目录和命令记录，不真正调用模型：

```bash
partpipeline run /path/to/model.glb --config configs/default.yaml --dry-run
```

## 3. 对已有 run 重新 bridge

如果 SAMPart3D 已经跑完，只想换一个 mask scale 或重新生成 multipart GLB：

```bash
partpipeline bridge outputs/runs/<run-id> --config configs/default.yaml
```

指定别的 SAMPart3D 分割尺度：

```bash
partpipeline bridge outputs/runs/<run-id> --config configs/default.yaml --mask-scale 1.5
```

## 4. 跑 HoloPart

```bash
partpipeline holopart outputs/runs/<run-id> --config configs/default.yaml
```

可覆盖推理参数：

```bash
partpipeline holopart outputs/runs/<run-id> \
  --config configs/default.yaml \
  --seed 42 \
  --num-inference-steps 50 \
  --guidance-scale 3.5 \
  --batch-size 8
```

## 5. 批处理

```bash
partpipeline batch inputs/phase7 --config configs/default.yaml
```

常用控制参数：

```bash
partpipeline batch inputs/phase7 \
  --config configs/default.yaml \
  --limit 2 \
  --skip-holopart
```

遇到失败立即停止：

```bash
partpipeline batch inputs/phase7 --config configs/default.yaml --stop-on-error
```

默认行为是 continue-on-error，也就是某个资产失败时继续处理后续资产，并把错误写进 `batch_manifest.json`。

## 6. 打包展示结果

```bash
partpipeline package outputs/runs/<run-id> --presentation-dir outputs/presentation
```

默认只输出 Level A：

- `level_a_segmented_parts.glb`

显式加入 HoloPart 对比结果：

```bash
partpipeline package outputs/runs/<run-id> \
  --presentation-dir outputs/presentation \
  --include-level-b
```

显式拷贝原始 GLB：

```bash
partpipeline package outputs/runs/<run-id> \
  --presentation-dir outputs/presentation \
  --include-original
```

## 7. 批量打包

```bash
partpipeline package-batch outputs/runs/batches/<batch-id>/batch_manifest.json \
  --presentation-dir outputs/presentation
```

打包时生成动画：

```bash
partpipeline package-batch outputs/runs/batches/<batch-id>/batch_manifest.json \
  --presentation-dir outputs/presentation \
  --generate-animation
```

## 8. 生成单个展示包动画

```bash
partpipeline animate outputs/presentation/<package-id> --config configs/default.yaml
```

调小渲染参数做快速检查：

```bash
partpipeline animate outputs/presentation/<package-id> \
  --config configs/default.yaml \
  --duration-seconds 2 \
  --fps 12 \
  --width 640 \
  --height 360
```

## 9. 测试

```bash
python -m unittest discover tests
```

完整模型链路依赖真实第三方工程和运行环境；单元测试主要验证配置、路径、manifest、runner 合约、bridge、presentation 和 animation 辅助逻辑。

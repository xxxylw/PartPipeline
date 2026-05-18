# PartPipeline 服务器运行模式

本文记录 Phase 7 的服务器友好运行方式。当前目标是让本地 WSL 的批处理路径和服务器路径保持同一套命令形状：先把输入放到 PartPipeline 管理目录，再运行 `batch`，输出由 manifest 统一记录。

## 已知服务器 SSH

```text
Host d5
    HostName 10.1.6.8
    User qzqd5
    Port 19091
```

这里不记录密码、token 或私钥路径。

## 本地 WSL 小样本流程

从 Windows 下载目录复制 GLB 到 PartPipeline 管理路径：

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli stage-inputs \
  /mnt/c/Users/qirui.huang/Downloads/assets/gt_glbs \
  --destination inputs/phase7 \
  --limit 3
```

运行批处理 dry-run：

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli batch \
  inputs/phase7 \
  --dry-run \
  --limit 2
```

运行真实批处理时去掉 `--dry-run`：

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli batch \
  inputs/phase7 \
  --limit 1
```

## 输出结构

批处理会生成一个批次 manifest：

```text
outputs/runs/batches/batch-<timestamp>/batch_manifest.json
```

每个资产仍然有自己的 run 目录：

```text
outputs/runs/<asset>-<timestamp>/
  manifest.json
  logs/
  sam/
  bridge/
  holopart/
```

`batch_manifest.json` 记录每个资产的：

- `asset_name`
- `input_path`
- `source_path`
- `run_dir`
- `manifest_path`
- `status`
- `error`

## 服务器 profile 形状

服务器配置目前在 `configs/default.yaml` 的 `server` profile 中保留占位路径。路径确认后，把这些占位值替换成服务器真实路径：

```text
project_root: /server/path/placeholder/PartPipeline
output_root: outputs/server-runs
sampart3d.python: /server/path/placeholder/miniconda3/envs/part/bin/python
holopart.python: /server/path/placeholder/miniconda3/envs/holopart/bin/python
```

服务器运行命令形状：

```bash
cd /server/path/placeholder/PartPipeline
PYTHONPATH=src /server/path/placeholder/miniconda3/envs/part/bin/python -m partpipeline.cli batch \
  inputs/phase7 \
  --profile server
```

## 注意事项

- 运行时不要直接依赖 Windows Downloads 路径；先用 `stage-inputs` 或服务器侧复制，把输入放进 `inputs/phase7`。
- `inputs/` 和 `outputs/` 都不提交到 git。
- SAMPart3D 仍使用 `part` 环境。
- HoloPart 仍使用 `holopart` 环境。
- HoloPart 权重不提交到 git；服务器上需要提前准备到 HoloPart 的 `pretrained_weights/HoloPart`。

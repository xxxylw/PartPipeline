# 环境与服务器

## 当前策略

PartPipeline v1 使用 dispatcher 策略：外部命令由同一个 CLI 统一编排，但 SAMPart3D 和 HoloPart 分别运行在各自已经验证过的环境中。

| 步骤 | 环境 | Python |
|------|------|--------|
| SAMPart3D | `part` | `/home/rui/miniconda3/envs/part/bin/python` |
| HoloPart | `holopart` | `/home/rui/miniconda3/envs/holopart/bin/python` |

这样做的原因是两个模型工程虽然都使用 PyTorch/CUDA，但依赖栈并不完全一致。直接把依赖混进同一个 live 环境有破坏已有可用环境的风险。

## 共享环境判断

已有环境探测显示：

- 两边 Python 都是 3.10。
- 两边 PyTorch/CUDA ABI 接近，存在未来合并环境的可能。
- `part` 环境更接近 SAMPart3D，包含 `torch_scatter` 和 `pointops`。
- `holopart` 环境更接近 HoloPart，包含 `diffusers`、`pymeshlab`、`torch_cluster` 等。
- NumPy、diffusers、transformers、huggingface_hub 等版本存在差异。

结论：v1 保持 dispatcher。若要尝试共享环境，应克隆一个新环境做 spike，不要直接修改现有 `part` 或 `holopart`。

## SAMPart3D 运行要点

SAMPart3D runner 会：

1. 把输入 GLB stage 到 run 的 `sam/` 目录。
2. 构造 `tools/run_sampart3d_object.py` 命令。
3. 检查输入、repo、Python、wrapper、config template、Blender、backbone weight。
4. 在 `outputs/run_state/part_cuda_lib` 中建立 CUDA 相关 `.so` symlink。
5. 通过 `LD_LIBRARY_PATH` 让 subprocess 找到 `libcudart` 和 `libnvrtc`。
6. 成功后复制选定的 `mesh_<scale>.npy` 到 run 的 `sam/` 目录。

## HoloPart 运行要点

HoloPart runner 使用：

- 输入：`bridge/prepared_parts.glb`
- 输出目录：`holopart/`
- 预期输出：`holopart/output.glb`

可配置参数包括：

- `seed`
- `num_inference_steps`
- `guidance_scale`
- `batch_size`
- `HF_ENDPOINT`

## 服务器信息

配置中保留了服务器 profile 与 SSH 信息：

```ssh-config
Host d5
  HostName 10.1.6.8
  User qzqd5
  Port 19091
```

服务器 profile 中的文件系统路径可能仍是 placeholder。正式跑服务器任务前，应先在服务器上确认：

- PartPipeline 仓库路径
- SAMPart3D/HoloPart 子模块路径
- conda 环境路径
- Blender/ffmpeg 路径
- 权重路径
- 输出目录权限

## 推荐排错顺序

1. `partpipeline run ... --dry-run` 确认配置和命令形状。
2. 检查 `manifest.json` 中记录的 command、cwd、env。
3. 查看 `logs/` 下 stdout/stderr。
4. 确认第三方 repo 和权重是否存在。
5. 确认 conda Python 路径是否存在。
6. 如果 SAMPart3D import 报 CUDA loader 问题，先检查 `outputs/run_state/part_cuda_lib` 和 `LD_LIBRARY_PATH`。

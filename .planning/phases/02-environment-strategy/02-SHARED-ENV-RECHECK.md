# Phase 2 共享环境复核

## 结论

当前不建议直接把现有 v1 pipeline 改成单环境运行。更准确的结论是：

- **现有 `part` 环境不能直接跑 HoloPart**：缺 `torch_cluster`、`diffusers`、`pymeshlab` 等 HoloPart 依赖。
- **现有 `holopart` 环境不能直接跑 SAMPart3D**：缺 `torch_scatter`、`pointops` 等 SAMPart3D 依赖。
- **新建一套共享环境有希望，但还没有被证明**：`part` 和 `holopart` 现在同为 `torch 2.1.0+cu121`，CUDA/PyTorch ABI 不再是明显冲突点。最现实路线是以 `part` 为底，补齐 HoloPart 依赖，并验证 HoloPart 是否接受 `numpy 1.26.4` 或是否必须降到 `numpy 1.22.3`。

所以 Phase 4 之前的建议仍然是：**保留 dispatcher 作为稳定路径，同时把“新建共享 env spike”作为可选实验，不要直接污染现有 `part` / `holopart` 环境。**

## 怎么复核

1. 用现有 `scripts/probe_env.py` 分别重新探测：
   - `/home/rui/miniconda3/envs/part/bin/python`
   - `/home/rui/miniconda3/envs/holopart/bin/python`
2. 对比两个项目的 `requirements.txt`：
   - `third_party/SAMPart3D/requirements.txt`
   - `third_party/HoloPart/requirements.txt`
3. 查看关键包版本：
   - `torch`
   - `torch_scatter`
   - `torch_cluster`
   - `numpy`
   - `diffusers`
   - `transformers`
   - `huggingface_hub`
   - `pymeshlab`
   - `pointops`
4. 在不修改 conda 环境本体的前提下，用项目输出目录中的 CUDA symlink 验证 `part` 环境能否加载 SAMPart3D 核心模块。

## 关键发现

| 项目 | `part` | `holopart` |
|------|--------|------------|
| Python | 3.10.20 | 3.10.20 |
| PyTorch | `2.1.0+cu121` | `2.1.0+cu121` |
| `torch_scatter` | 可用，`2.1.2+pt21cu121` | 缺失 |
| `torch_cluster` | 缺失 | 可用，`1.6.3+pt21cu121` |
| `pointops` | 可用，`1.0` | 缺失 |
| `diffusers` | 缺失 | 可用，`0.30.3` |
| `pymeshlab` | 缺失 | 可用，`2025.7.post1` |
| `numpy` | `1.26.4` | `1.22.3` |
| `transformers` | `4.37.2` | `4.44.2` |
| `huggingface_hub` | `0.36.2` | `0.24.6` |

## Smoke Test 结果

| Smoke test | `part` | `holopart` |
|------------|--------|------------|
| SAMPart3D runner `--help` | pass | pass |
| SAMPart3D core import | 原始失败：`libcudart.so` loader path；加临时 symlink 后核心模块可分别 import | fail：缺 `pointops` |
| HoloPart inference `--help` | fail：缺 `pymeshlab` | pass |
| HoloPart core import | fail：缺 `diffusers` | pass |

额外验证：

- 在 `outputs/run_state/part_cuda_lib/` 中建立 `libcudart.so` 和 `libnvrtc.so` 临时 symlink 后，`part` 环境可以分别 import：
  - `pointcept.datasets`
  - `pointcept.engines.train`
  - `pointcept.engines.eval`
  - `pointcept.models`
- 同一个 Python 进程里连续 import `train` 和 `eval` 会触发 `multiprocessing context has already been set`，这更像 SAMPart3D import side-effect，不是环境合并阻塞点。

## 为什么还不直接合并

直接合并现有环境有三个风险：

1. **污染工作环境**：`part` 是当前最接近 SAMPart3D 的环境，直接往里面装 HoloPart 依赖可能破坏 Phase 4。
2. **NumPy 约束不确定**：HoloPart requirements pin 了 `numpy==1.22.3`，但 `part` 是 `numpy==1.26.4`。是否必须降级，需要实际 HoloPart import/prepare_data/inference 验证。
3. **transformers / huggingface_hub 版本差异**：两个环境版本不同，可能在模型加载或 pipeline 初始化时才暴露问题。

## 推荐下一步

如果要继续追求一套环境，建议新建独立 spike 环境，例如：

```bash
conda create -n partpipeline-shared --clone part
```

然后只在这个新环境里补 HoloPart 缺失依赖：

```bash
conda activate partpipeline-shared
pip install diffusers==0.30.3 pymeshlab==2025.7.post1 torch-cluster==1.6.3+pt21cu121
```

实际安装命令可能需要使用 PyTorch Geometric 对应 wheel index。安装后必须通过这些 gates：

1. SAMPart3D runner `--help` pass。
2. SAMPart3D core modules import pass，且 CUDA loader symlink 策略可复现。
3. HoloPart inference `--help` pass。
4. HoloPart core import pass。
5. 不降级/破坏 `torch_scatter`、`pointops`、`torch`。

只有这些 gates 都通过，才值得把 `configs/default.yaml` 从 dispatcher 改成 shared env。否则继续用 dispatcher 更稳。

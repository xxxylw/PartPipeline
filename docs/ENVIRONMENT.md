# 环境配置手册：Level A 优先，Level B 可选

这份文档给服务器端 agent 使用。当前项目的推荐部署逻辑是：

1. **只想跑默认拆件展示 Level A**：只需要配置 `part` 环境。
2. **以后还想跑 HoloPart Level B**：再额外配置 `holopart` 环境。
3. 不推荐一开始强行合并成一个环境。我们已经做过统一环境 spike，结论见文末。

## 环境分工

| 输出目标 | 必需环境 | 需要安装 HoloPart 吗 | 说明 |
|----------|----------|----------------------|------|
| Level A | `part` | 不需要 | SAMPart3D 分割 + PartPipeline bridge + 展示包 |
| Level A + 视频 | `part` | 不需要 | 在 Level A 基础上加 Blender/ffmpeg |
| Level B | `part` + `holopart` | 需要 | 先有 Level A/bridge，再把结果交给 HoloPart |

所以如果服务器端按钮只是“输入 GLB，输出拆件结果”，默认只装 `part` 就够了。

## 0. 从 conda 开始

如果服务器已经有 conda，可以跳到第 1 节。下面假设安装到：

```text
$HOME/miniconda3
```

安装 Miniconda：

```bash
cd ~
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p "$HOME/miniconda3"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda init bash
source ~/.bashrc
```

确认：

```bash
conda --version
```

检查 GPU：

```bash
nvidia-smi
```

如果 `nvidia-smi` 不可用，先修 NVIDIA Driver，不要继续配模型环境。

## 1. 拉取 PartPipeline

建议服务器路径：

```bash
mkdir -p /home/qzqd5/of_work/code
cd /home/qzqd5/of_work/code
git clone git@github.com:xxxylw/PartPipeline.git
cd PartPipeline
git submodule update --init --recursive
```

确认子模块：

```bash
git submodule status --recursive
ls third_party/SAMPart3D
ls third_party/HoloPart
```

如果当前只做 Level A，`third_party/HoloPart` 可以先存在但不用配置环境、不用下载权重。

## 2. Level A：创建 `part` 环境

`part` 环境负责：

- PartPipeline CLI
- SAMPart3D 分割
- Level A bridge
- 展示包打包
- 可选动画渲染

创建环境：

```bash
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda create -n part python=3.10 -y
conda activate part
```

安装 PyTorch CUDA 12.1：

```bash
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121
```

安装 PartPipeline：

```bash
cd /home/qzqd5/of_work/code/PartPipeline
pip install -e .
```

安装 SAMPart3D Python 依赖：

```bash
cd /home/qzqd5/of_work/code/PartPipeline/third_party/SAMPart3D
pip install -r requirements.txt
```

如果 `torch-scatter` 从源码编译失败，使用 PyG 对应 PyTorch/CUDA wheel：

```bash
pip install torch-scatter -f https://data.pyg.org/whl/torch-2.1.0+cu121.html
```

安装 SAMPart3D 的 `pointops`：

```bash
cd /home/qzqd5/of_work/code/PartPipeline/third_party/SAMPart3D/libs/pointops
python setup.py install
```

安装 `spconv`：

```bash
pip install spconv-cu120
```

安装 SAMPart3D 加速依赖：

```bash
pip install ninja
pip install git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch
pip install --extra-index-url=https://pypi.nvidia.com cudf-cu11==24.6.* cuml-cu11==24.6.*
```

如果 RAPIDS 相关包安装失败，先不要改环境。先记录报错，再根据服务器 CUDA/driver 单独处理。Level A 的路径检查可以先用 dry-run 做。

## 3. Level A：准备 SAMPart3D 权重

SAMPart3D 需要 PTv3-object backbone。PartPipeline 默认检查：

```text
third_party/SAMPart3D/ckpt/ptv3-object.pth
```

创建目录：

```bash
cd /home/qzqd5/of_work/code/PartPipeline/third_party/SAMPart3D
mkdir -p ckpt
```

下载或上传权重到：

```text
/home/qzqd5/of_work/code/PartPipeline/third_party/SAMPart3D/ckpt/ptv3-object.pth
```

确认：

```bash
ls -lh /home/qzqd5/of_work/code/PartPipeline/third_party/SAMPart3D/ckpt/ptv3-object.pth
```

如果服务器访问 Hugging Face 慢，可以在本地下载后上传到这个路径。

## 4. Level A 可选：安装 Blender 和 ffmpeg

如果只要 `level_a_segmented_parts.glb` 和 `parts/part_001.glb`，可以先不装 Blender/ffmpeg。

如果要导出拆件动画视频，则在 `part` 环境里安装：

```bash
conda activate part
conda install -c conda-forge ffmpeg -y
```

安装 Blender 官方 Linux 版本：

```bash
conda activate part
mkdir -p "$CONDA_PREFIX/opt"
cd "$CONDA_PREFIX/opt"
wget https://download.blender.org/release/Blender4.5/blender-4.5.0-linux-x64.tar.xz
tar -xf blender-4.5.0-linux-x64.tar.xz
rm blender-4.5.0-linux-x64.tar.xz
ln -sf "$CONDA_PREFIX/opt/blender-4.5.0-linux-x64/blender" "$CONDA_PREFIX/bin/blender"
```

验证：

```bash
blender --version
ffmpeg -version | head
```

服务器没有桌面环境也可以，PartPipeline 使用 Blender background 模式。

## 5. Level A：验证 `part` 环境

```bash
conda activate part
python - <<'PY'
import torch
import torchvision
import numpy
import trimesh
import open3d
import transformers
import torch_scatter
import pointops
import spconv
print("torch", torch.__version__, "cuda", torch.version.cuda, "available", torch.cuda.is_available())
print("torchvision", torchvision.__version__)
print("numpy", numpy.__version__)
print("trimesh", trimesh.__version__)
print("open3d", open3d.__version__)
print("transformers", transformers.__version__)
print("part env ok")
PY
```

本地已验证版本参考：

```text
Python 3.10.20
torch 2.1.0+cu121
torchvision 0.16.0+cu121
numpy 1.26.4
trimesh 4.11.5
open3d 0.19.0
transformers 4.37.2
torch_scatter 2.1.2+pt21cu121
spconv 2.3.6
```

## 6. 配置 `server` profile

默认配置文件：

```text
configs/default.yaml
```

如果只跑 Level A，重点保证 `server.project_root`、`server.output_root`、`server.sampart3d.python` 正确。`holopart` 可以先保留模板，不影响 `--skip-holopart` 的 Level A 流程。

示例：

```yaml
profiles:
  server:
    project_root: /home/qzqd5/of_work/code/PartPipeline
    output_root: outputs/server-runs
    filesystem_paths_are_placeholders: false
    ssh:
      host_alias: d5
      hostname: 10.1.6.8
      user: qzqd5
      port: 19091
    sampart3d:
      repo: third_party/SAMPart3D
      env: part
      python: /home/qzqd5/miniconda3/envs/part/bin/python
      default_mask_scale: "1.0"
    holopart:
      repo: third_party/HoloPart
      env: holopart
      python: /home/qzqd5/miniconda3/envs/holopart/bin/python
      hf_endpoint: https://hf-mirror.com
      weights_dir: pretrained_weights/HoloPart
```

动画路径在同一个配置文件里：

```yaml
pipeline:
  animation:
    blender: /home/qzqd5/miniconda3/envs/part/bin/blender
    ffmpeg: /home/qzqd5/miniconda3/envs/part/bin/ffmpeg
```

如果没有安装 Blender/ffmpeg，先不要执行 `animate` 或 `package-batch --generate-animation`。

## 7. Level A：跑单个 GLB

进入项目：

```bash
cd /home/qzqd5/of_work/code/PartPipeline
```

推荐服务器上始终显式写 `PYTHONPATH=src`。

先检查 CLI：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli --help
```

先 dry-run 检查路径：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli run /path/to/model.glb \
  --config configs/default.yaml \
  --profile server \
  --dry-run
```

真实跑 SAMPart3D：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli run /path/to/model.glb \
  --config configs/default.yaml \
  --profile server
```

命令结束会打印：

```text
Run directory: outputs/server-runs/<glb-name>-<timestamp>
Manifest: outputs/server-runs/<glb-name>-<timestamp>/manifest.json
```

生成 Level A bridge：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli bridge outputs/server-runs/<run-id> \
  --config configs/default.yaml \
  --profile server
```

打包展示结果：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli package outputs/server-runs/<run-id> \
  --presentation-dir outputs/presentation
```

Level A 输出：

```text
outputs/presentation/<glb-name>-<timestamp>/level_a_segmented_parts.glb
outputs/presentation/<glb-name>-<timestamp>/parts/part_001.glb
outputs/presentation/<glb-name>-<timestamp>/parts/part_002.glb
outputs/presentation/<glb-name>-<timestamp>/parts/parts_manifest.json
```

如果要视频：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli animate outputs/presentation/<package-id> \
  --config configs/default.yaml \
  --width 960 \
  --height 540
```

视频输出：

```text
outputs/presentation/<package-id>/animation/exploded_assembly.mp4
```

## 8. Level A：批处理

只跑 Level A，推荐显式加 `--skip-holopart`：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli batch /path/to/glb_dir \
  --config configs/default.yaml \
  --profile server \
  --skip-holopart
```

批处理 manifest：

```text
outputs/server-runs/batches/<batch-id>/batch_manifest.json
```

批量打包：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli package-batch outputs/server-runs/batches/<batch-id>/batch_manifest.json \
  --presentation-dir outputs/presentation
```

批量打包并生成视频：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli package-batch outputs/server-runs/batches/<batch-id>/batch_manifest.json \
  --presentation-dir outputs/presentation \
  --generate-animation \
  --width 640 \
  --height 360
```

## 9. 以后需要 Level B：创建 `holopart` 环境

Level B 是可选功能。只有需要调用 HoloPart 时才做本节。

创建环境：

```bash
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda create -n holopart python=3.10 -y
conda activate holopart
```

安装 PyTorch CUDA 12.1：

```bash
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
```

安装 HoloPart requirements：

```bash
cd /home/qzqd5/of_work/code/PartPipeline/third_party/HoloPart
pip install -r requirements.txt
```

如果 `torch-cluster` 从源码编译失败，使用 PyG wheel：

```bash
pip install torch-cluster -f https://data.pyg.org/whl/torch-2.1.0+cu121.html
```

如果 `diso`、`pymeshlab` 或其他包失败，先保存完整错误日志，再根据服务器系统库和 CUDA 情况处理。

## 10. Level B：准备 HoloPart 权重和镜像

HoloPart 默认使用 Hugging Face 权重。项目配置里已经使用镜像：

```yaml
hf_endpoint: https://hf-mirror.com
```

也可以在 shell 里显式设置：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

推荐提前准备权重目录：

```text
third_party/HoloPart/pretrained_weights/HoloPart
```

本地已有的权重结构参考：

```text
third_party/HoloPart/pretrained_weights/HoloPart/part_encoder/diffusion_pytorch_model.safetensors
third_party/HoloPart/pretrained_weights/HoloPart/transformer/diffusion_pytorch_model.safetensors
third_party/HoloPart/pretrained_weights/HoloPart/vae/diffusion_pytorch_model.safetensors
```

确认：

```bash
ls -R /home/qzqd5/of_work/code/PartPipeline/third_party/HoloPart/pretrained_weights/HoloPart | head -80
```

## 11. Level B：验证 `holopart` 环境

```bash
conda activate holopart
python - <<'PY'
import torch
import torchvision
import numpy
import trimesh
import transformers
import diffusers
import huggingface_hub
import pymeshlab
import torch_cluster
import diso
import peft
print("torch", torch.__version__, "cuda", torch.version.cuda, "available", torch.cuda.is_available())
print("torchvision", torchvision.__version__)
print("numpy", numpy.__version__)
print("transformers", transformers.__version__)
print("diffusers", diffusers.__version__)
print("huggingface_hub", huggingface_hub.__version__)
print("holopart env ok")
PY
```

本地已验证版本参考：

```text
Python 3.10.20
torch 2.1.0+cu121
torchvision 0.16.0+cu121
numpy 1.22.3
trimesh 4.12.1
transformers 4.44.2
diffusers 0.30.3
huggingface_hub 0.24.6
torch_cluster 1.6.3+pt21cu121
peft 0.12.0
```

## 12. Level B：运行 HoloPart

Level B 必须在已有 Level A bridge 的 run 上执行。也就是说，先有：

```text
outputs/server-runs/<run-id>/bridge/prepared_parts.glb
```

再运行：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli holopart outputs/server-runs/<run-id> \
  --config configs/default.yaml \
  --profile server
```

注意：入口命令仍然用 `part` 环境运行 PartPipeline CLI；PartPipeline 内部会根据 profile 调用：

```text
/home/qzqd5/miniconda3/envs/holopart/bin/python
```

HoloPart 输出：

```text
outputs/server-runs/<run-id>/holopart/output.glb
```

打包时带上 Level B：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli package outputs/server-runs/<run-id> \
  --presentation-dir outputs/presentation \
  --include-level-b
```

## 13. 服务器按钮接入建议

按钮触发时，推荐默认只跑 Level A：

```json
{
  "input_glb": "/data/uploads/model.glb",
  "level": "A",
  "render_video": false
}
```

后台执行：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli run "$INPUT_GLB" --config configs/default.yaml --profile server
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli bridge "$RUN_DIR" --config configs/default.yaml --profile server
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli package "$RUN_DIR" --presentation-dir outputs/presentation
```

如果 `render_video=true`，再执行：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli animate "$PACKAGE_DIR" --config configs/default.yaml --width 960 --height 540
```

如果以后要 Level B，API 参数可以变成：

```json
{
  "input_glb": "/data/uploads/model.glb",
  "level": "B",
  "render_video": false
}
```

然后在 Level A bridge 后追加：

```bash
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli holopart "$RUN_DIR" --config configs/default.yaml --profile server
PYTHONPATH=src /home/qzqd5/miniconda3/bin/conda run -n part python -m partpipeline.cli package "$RUN_DIR" --presentation-dir outputs/presentation --include-level-b
```

推荐做异步 job，不要让 HTTP 请求同步等待模型跑完：

```text
queued -> running_sampart3d -> bridge_complete -> packaging -> complete
```

如果带 Level B：

```text
queued -> running_sampart3d -> bridge_complete -> running_holopart -> packaging -> complete
```

## 14. 常见问题

### 只跑 Level A 是否要安装 HoloPart？

不需要。只要命令里使用 `--skip-holopart`，或者只执行 `run -> bridge -> package`，就不会调用 HoloPart。

### 只跑 Level A 是否要安装 Blender？

不一定。只输出 GLB 和 parts 不需要 Blender/ffmpeg。只有执行 `animate` 或 `package-batch --generate-animation` 才需要。

### SAMPart3D 报缺少 `ptv3-object.pth`

检查：

```bash
ls -lh third_party/SAMPart3D/ckpt/ptv3-object.pth
```

没有的话，把权重放到这个路径。

### `pointops` 编译失败

优先确认：

```bash
conda activate part
python - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
PY
```

如果报 CUDA header、`nvcc`、`cuda_runtime.h` 之类问题，说明服务器缺 CUDA 编译链或版本不匹配。不要改 HoloPart，先把 `part` 环境修到 `pointops` 可 import。

### HoloPart 下载权重失败

设置镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

或者提前把权重上传到：

```text
third_party/HoloPart/pretrained_weights/HoloPart
```

## 15. 最小成功标准

只跑 Level A 时，成功标准是：

1. `conda run -n part python -m partpipeline.cli --help` 正常。
2. `part` 环境能 import `torch`、`pointops`、`torch_scatter`、`spconv`。
3. 一个测试 `.glb` 能跑出：

```text
outputs/server-runs/<run-id>/sam/mesh_1.0.npy
outputs/server-runs/<run-id>/bridge/prepared_parts.glb
outputs/presentation/<package-id>/level_a_segmented_parts.glb
```

需要 Level B 时，再增加成功标准：

1. `holopart` 环境能 import `diffusers`、`pymeshlab`、`torch_cluster`、`diso`。
2. 已有 Level A bridge 的 run 能跑出：

```text
outputs/server-runs/<run-id>/holopart/output.glb
```

## 16. 为什么不推荐统一环境

2026-05-21 做过一次隔离 spike，环境名为 `partpipeline-unified`。结论是：**单环境有理论可行性，但当前不推荐作为默认服务器方案**。

主要原因：

- HoloPart 的 `numpy==1.22.3` 会和 PartPipeline/open3d/opencv/matplotlib/pandas 一侧冲突。
- 折中到 `numpy==1.24.4` 后，大部分普通包可以 import。
- `diso` 虽然能编译安装，但最终 import 出现 `undefined symbol`。
- SAMPart3D 的 `pointops` 对 CUDA 编译链很敏感，补装 `cuda-nvcc` 和 `cuda-toolkit` 时容易混入 CUDA 13.x headers，而 PyTorch 是 cu121，导致编译链不稳定。

所以当前生产建议是：

```text
Level A 默认路径：part 环境
Level B 可选路径：part 调度 holopart 环境
```

如果以后要正式做单环境，应该单独开环境工程任务，固定 PyTorch cu121、CUDA toolkit/dev headers 12.1，并先把 `pointops` 和 `diso` wheel 化后再尝试切换。

# 配置说明

默认配置文件是 `configs/default.yaml`。CLI 默认读取它，也可以通过 `--config` 指定其他 YAML。

## 顶层结构

配置包含四块：

- `active_profile`
- `environment`
- `pipeline`
- `profiles`

`src/partpipeline/config.py` 会校验这些字段，并把相对路径解析到项目根目录下。

## active_profile

`active_profile` 是没有传 `--profile` 时使用的默认 profile。当前默认是：

```yaml
active_profile: local_wsl
```

## environment

当前策略是：

```yaml
environment:
  strategy: dispatcher
  shared_env_feasible: false
```

含义是：用户面对的是一个统一的 `partpipeline` 命令，但内部分别用适合 SAMPart3D 和 HoloPart 的 Python 环境运行 subprocess。

## pipeline

关键默认值：

```yaml
pipeline:
  default_mask_scale: "1.0"
  keep_intermediates: true
  bridge:
    merge_small_parts: true
    min_faces_per_part: 100
    min_area_ratio: 0.001
    validate_holopart_prepare_data: false
```

`default_mask_scale` 决定默认选择哪个 SAMPart3D mask，例如 `mesh_1.0.npy`。

Bridge 参数含义：

- `merge_small_parts`：是否把小碎片合并到邻近大部件。
- `min_faces_per_part`：低于该面数的 label 视为小碎片。
- `min_area_ratio`：低于该比例的 label 视为小碎片。
- `validate_holopart_prepare_data`：是否额外校验 HoloPart prepare_data 兼容性。

## animation

动画参数位于 `pipeline.animation`：

- `blender`：Blender 可执行文件。
- `ffmpeg`：ffmpeg 可执行文件。
- `default_duration_seconds`：默认时长。
- `fps`：帧率。
- `width`、`height`：输出分辨率。
- `explode_scale`：部件向外炸开的距离比例。
- `rotation_degrees`：部件炸开时的轻微旋转角度。

`animate` 和 `package-batch --generate-animation` 都可以通过 CLI 覆盖这些值。

## profiles

每个 profile 包含：

- `project_root`
- `output_root`
- `sampart3d`
- `holopart`
- 可选 `ssh`

工具配置块通常包含：

- `repo`
- `env`
- `python`
- 工具特定参数，例如权重路径、Blender 路径、HF endpoint、seed、steps、guidance scale、batch size。

## local_wsl

`local_wsl` 是当前主要开发 profile：

- SAMPart3D 使用 `part` 环境。
- HoloPart 使用 `holopart` 环境。
- 输出默认写到 `outputs/runs`。

## server

`server` 是服务器运行模板。它记录了 SSH 信息，但文件系统路径仍可能是 placeholder，需要在服务器上实际确认后再使用。

# Phase 6 Verification

## 验证结论

Phase 6 通过。PartPipeline 已经能够对 Phase 5 的 `bridge/prepared_parts.glb` 调用真实 HoloPart，并收集 `holopart/output.glb`。manifest 最终状态为 `holopart_complete`。

## 自动化测试

命令：

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m unittest discover -s tests
```

结果：

```text
Ran 32 tests in 0.432s
OK
```

覆盖点：

1. HoloPart 默认配置可加载。
2. runner dry-run command 和 env 正确。
3. 缺少 `prepared_parts.glb` 会在 preflight 阶段失败。
4. 子进程成功但缺少 `output.glb` 会被视为失败。
5. orchestration 会保留已有 `sampart3d` 和 `bridge` manifest 段。
6. CLI 成功时打印 output 和 manifest 路径，失败时给出清晰错误。

## 真实推理验证

命令：

```bash
cd /home/rui/of_work/code/PartPipeline
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli holopart outputs/runs/08.toulouse-20260515-160213
```

结果：

```text
Profile: local_wsl
Status: holopart_complete
Output GLB: /home/rui/of_work/code/PartPipeline/outputs/runs/08.toulouse-20260515-160213/holopart/output.glb
Manifest: /home/rui/of_work/code/PartPipeline/outputs/runs/08.toulouse-20260515-160213/manifest.json
```

输出文件：

```text
/home/rui/of_work/code/PartPipeline/outputs/runs/08.toulouse-20260515-160213/holopart/output.glb
```

文件大小：

```text
6771444 bytes
```

`trimesh` 加载验证：

```text
status=holopart_complete
loaded_type=Scene
geometry_count=34
```

## 权重下载说明

第一次真实运行失败在 Hugging Face 权重下载阶段，错误来自 `huggingface_hub.snapshot_download` 的 metadata/cache 链路。runner 已经按要求设置了：

```text
HF_ENDPOINT=https://hf-mirror.com
```

但 Python hub 客户端仍未能通过镜像链路完成下载。本次解决方式是用 `curl -L -C -` 把 HoloPart 权重预下载到：

```text
/home/rui/of_work/code/PartPipeline/third_party/HoloPart/pretrained_weights/HoloPart
```

随后重新执行同一条 PartPipeline HoloPart 命令，真实推理成功。

权重不提交到 git。

## 验收项

- [x] PartPipeline 可以调用 HoloPart 处理 prepared GLB。
- [x] `holopart/output.glb` 写入 run 输出目录。
- [x] stdout/stderr 日志写入 run logs。
- [x] `manifest.json` 更新为 `holopart_complete`。
- [x] 失败时会记录 `error.type = holopart` 和日志路径。
- [x] 真实输出 GLB 可以被 `trimesh` 加载。

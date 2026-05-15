# Phase 6 Summary: HoloPart Integration

## 本阶段目标

Phase 6 的目标是把 Phase 5 生成的 HoloPart 输入 `bridge/prepared_parts.glb` 接入真实 HoloPart 推理，产出补全后的 `holopart/output.glb`，并把命令、日志、状态和输出路径写回同一个 run 的 `manifest.json`。

## 已完成内容

1. 增加 HoloPart 配置默认值：
   - `HF_ENDPOINT=https://hf-mirror.com`
   - seed: `42`
   - inference steps: `50`
   - guidance scale: `3.5`
   - batch size: `8`
   - weights dir: `pretrained_weights/HoloPart`
2. 增加 HoloPart runner：
   - 检查 `bridge/prepared_parts.glb` 是否存在。
   - 检查 HoloPart repo、python、`scripts/inference_holopart.py` 是否存在。
   - 使用 HoloPart 自己的 `holopart` conda 环境执行推理。
   - 统一把 stdout/stderr 写入 run 目录下的 logs。
   - 推理成功后要求 `holopart/output.glb` 必须存在。
3. 增加编排层接口：
   - `run_holopart_for_existing_run(...)`
   - 读取已有 `manifest.json`。
   - 保留 `sampart3d` 和 `bridge` 段。
   - 追加 HoloPart command 记录。
   - 成功时设置 `status = holopart_complete`。
   - 失败时设置 `status = failed` 和 `error.type = holopart`。
4. 增加 CLI：
   - `partpipeline holopart <run_dir>`
   - 支持 `--seed`、`--num-inference-steps`、`--guidance-scale`、`--batch-size` 覆盖默认值。
5. 真实跑通：
   - 输入 run: `outputs/runs/08.toulouse-20260515-160213`
   - 输入: `bridge/prepared_parts.glb`
   - 输出: `holopart/output.glb`
   - 最终状态: `holopart_complete`

## 重要实现决策

本阶段没有强行把 SAMPart3D 和 HoloPart 合并到同一个 Python 环境。PartPipeline 的用户入口仍然是统一命令，但内部按照配置调用 HoloPart 对应的 conda python。这样后续上传到服务器时更稳，也更容易把模型环境问题隔离在 runner 层。

Hugging Face 镜像保持打开：runner 默认注入 `HF_ENDPOINT=https://hf-mirror.com`。真实运行时，HoloPart 的 Python 下载链路遇到了 mirror metadata/cache 问题，所以本次把权重手动预下载到了 `third_party/HoloPart/pretrained_weights/HoloPart`，再运行推理成功。这个处理不把大权重提交进 git。

## 现在怎么用

在 WSL 里进入项目：

```bash
cd /home/rui/of_work/code/PartPipeline
```

对已经完成 Phase 5 bridge 的 run 执行：

```bash
PYTHONPATH=src /home/rui/miniconda3/envs/part/bin/python -m partpipeline.cli holopart outputs/runs/08.toulouse-20260515-160213
```

成功后看：

```text
outputs/runs/08.toulouse-20260515-160213/holopart/output.glb
outputs/runs/08.toulouse-20260515-160213/logs/holopart.stdout.log
outputs/runs/08.toulouse-20260515-160213/logs/holopart.stderr.log
outputs/runs/08.toulouse-20260515-160213/manifest.json
```

## 下一阶段建议

Phase 7 做批处理、服务器运行模式和展示输出。也就是把现在单个 run 跑通的链路扩展成文件夹队列，并把服务器 `d5` 的使用方式、输出组织、展示素材一起补完整。

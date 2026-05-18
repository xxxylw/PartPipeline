# Phase 7 Summary: Batch Runtime And Server-Ready Paths

## 本阶段目标

Phase 7 把前面已经跑通的单资产链路扩展成批处理骨架：先把输入 GLB 复制到 PartPipeline 管理路径，再对目录运行 batch，并用 batch manifest 汇总每个资产的 run 目录、manifest、状态和错误。

## 已完成内容

1. 增加输入 staging：
   - 新命令：`partpipeline stage-inputs`
   - 输入源可以是 `/mnt/c/Users/qirui.huang/Downloads/assets/gt_glbs`
   - 输出到 `inputs/phase7`
   - 写入 `inputs/phase7/input_manifest.json`
2. 增加 batch manifest：
   - 新增 `BatchItemResult`
   - 新增 `BatchManifest`
   - 新增 `create_batch_dir`
   - 新增 `write_batch_manifest`
3. 实现真实 batch 编排：
   - 新函数：`run_batch_pipeline(...)`
   - 对目录内 `.glb` 逐个创建独立 run
   - dry-run 时不会触发真实模型
   - 非 dry-run 时按现有链路串起 SAMPart3D -> bridge -> HoloPart
   - 默认 continue-on-error，失败资产会写入 batch manifest
4. 替换原来的 `batch` 占位命令：
   - 支持 `--dry-run`
   - 支持 `--limit`
   - 支持 `--stop-on-error`
   - 支持 `--skip-holopart`
   - 支持 `--mask-scale`
5. 增加服务器运行文档：
   - `docs/server-run-mode.md`
   - 记录 `d5` SSH 信息
   - 记录本地和服务器命令形状

## 关键文件

- `.gitignore`
- `src/partpipeline/inputs.py`
- `src/partpipeline/types.py`
- `src/partpipeline/artifacts.py`
- `src/partpipeline/orchestrator.py`
- `src/partpipeline/cli.py`
- `tests/test_inputs.py`
- `tests/test_batch_orchestrator.py`
- `tests/test_cli.py`
- `docs/server-run-mode.md`

## 保持延期的内容

以下内容没有放进 Phase 7，继续留给 Phase 8：

- per-part exports
- presentation 汇总目录
- HTML report
- preview images

Phase 7 先保证批处理生产线和路径管理稳定。

---
phase: 3
phase_name: Runtime Configuration and Layered Core
status: validated
nyquist_compliant: true
validated_at: 2026-05-15
---

# Phase 3 Validation：运行时配置与分层核心

## 为什么要做这次验证

Phase 3 已经完成并通过基础 verification，但 verification 主要证明“现在能跑通”。Nyquist validation 要多看一层：每个阶段承诺的行为，是否都有自动化测试守住。这样后面 Phase 4 接入真实 SAMPart3D 时，如果 CLI 参数、profile 解析、manifest 格式或 runner 契约被不小心改坏，测试会尽早报警。

这次验证保持 Phase 3 的边界：不运行 SAMPart3D，不运行 HoloPart，不访问服务器，不安装依赖。

## 怎么做

1. 读取 Phase 3 的 `03-PLAN.md`、`03-SUMMARY.md` 和 `03-VERIFICATION.md`。
2. 把 Phase 3 涉及的需求映射到具体任务：
   - `CLI-01`：单文件 `run` 命令。
   - `CLI-02`：目录级 `batch` 命令。
   - `CLI-03`：mask scale 默认值与覆盖。
   - `OUT-01`：run artifact 与 `manifest.json`。
   - `ENV-02`：用户只面对统一 PartPipeline CLI，内部保留 dispatcher/profile 策略。
3. 扫描现有测试：
   - `tests/test_config.py`
   - `tests/test_artifacts.py`
   - `tests/test_runner.py`
   - `tests/test_orchestrator.py`
   - `tests/test_probe_env.py`
4. 发现 CLI 层有直接覆盖缺口后，新增 `tests/test_cli.py`：
   - 验证 `run --dry-run` 能写 manifest。
   - 验证 `--mask-scale 2.0` 会覆盖配置默认值。
   - 验证 `batch --dry-run` 会加载 profile 并统计 `.glb` 数量。
5. 重新运行完整测试和编译检查。

## 测试基础设施

| 项目 | 内容 |
|------|------|
| 测试框架 | Python `unittest` |
| CLI 测试工具 | `typer.testing.CliRunner` |
| 运行环境 | `/home/rui/miniconda3/envs/p3sam/bin/python` |
| 测试命令 | `PYTHONPATH=src /home/rui/miniconda3/envs/p3sam/bin/python -m unittest discover -s tests` |
| 编译检查 | `/home/rui/miniconda3/envs/p3sam/bin/python -m py_compile src/partpipeline/*.py src/partpipeline/runners/*.py scripts/probe_env.py` |

## 需求覆盖矩阵

| 需求 | 状态 | 自动化覆盖 |
|------|------|------------|
| CLI-01 | COVERED for Phase 3 scope | `tests/test_cli.py::test_run_command_writes_manifest_and_applies_mask_override` 和 `tests/test_orchestrator.py` 验证单文件 dry-run 会创建 manifest。 |
| CLI-02 | COVERED for Phase 3 scope | `tests/test_cli.py::test_batch_command_loads_profile_and_counts_glbs` 验证 batch 命令加载 profile 并统计 `.glb`。 |
| CLI-03 | COVERED for Phase 3 scope | `tests/test_config.py` 验证默认 `1.0`，`tests/test_cli.py` 验证 CLI 覆盖为 `2.0`。 |
| OUT-01 | COVERED for Phase 3 scope | `tests/test_artifacts.py` 和 `tests/test_orchestrator.py` 验证目录布局、manifest 内容、命令契约。 |
| ENV-02 | COVERED for Phase 3 scope | `tests/test_config.py` 验证 `local_wsl` / `server` profile，`tests/test_cli.py` 验证统一 CLI 使用 profile。 |

## 手动验证项

| 项目 | 原因 |
|------|------|
| 真实 SAMPart3D 执行 | Phase 3 明确不运行模型，留到 Phase 4。 |
| 真实 HoloPart 执行 | Phase 3 明确不运行模型，留到 Phase 6。 |
| 服务器 `d5` 文件系统路径 | Phase 3 只记录 SSH 身份和占位路径，不检查服务器。 |

## 验证结果

Phase 3 现在满足本阶段范围内的 Nyquist validation：每个 Phase 3 承诺的可自动验证行为都有测试覆盖。剩余项不是缺口，而是后续阶段的目标。

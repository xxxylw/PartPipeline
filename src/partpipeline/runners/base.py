from __future__ import annotations

import os
import subprocess
from pathlib import Path

from partpipeline.types import CommandResult


class SubprocessRunner:
    def run(
        self,
        command: list[str],
        cwd: Path,
        logs_dir: Path,
        name: str,
        env: dict[str, str] | None = None,
        dry_run: bool = False,
    ) -> CommandResult:
        logs_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = logs_dir / f"{name}.stdout.log"
        stderr_log = logs_dir / f"{name}.stderr.log"
        merged_env = dict(env or {})

        if dry_run:
            stdout_log.write_text(
                "DRY RUN: command was recorded but not executed.\n"
                + " ".join(command)
                + "\n",
                encoding="utf-8",
            )
            stderr_log.write_text("", encoding="utf-8")
            return CommandResult(
                command=command,
                cwd=cwd,
                exit_code=None,
                stdout_log=stdout_log,
                stderr_log=stderr_log,
                dry_run=True,
                env=merged_env,
            )

        process_env = os.environ.copy()
        process_env.update(merged_env)
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=process_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        stdout_log.write_text(completed.stdout, encoding="utf-8")
        stderr_log.write_text(completed.stderr, encoding="utf-8")

        return CommandResult(
            command=command,
            cwd=cwd,
            exit_code=completed.returncode,
            stdout_log=stdout_log,
            stderr_log=stderr_log,
            dry_run=False,
            env=merged_env,
        )
